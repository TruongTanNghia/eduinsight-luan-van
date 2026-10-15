"""Các mô hình học sâu trong đề cương (mục 5.4, 5.6), cùng giao diện:

    forward(xs, m, st) -> (reg [B, n_targets], logits [B, n_classes])

xs: [B, S, T] điểm đã chuẩn hóa (ô khuyết = 0), m: [B, S, T] mặt nạ (1 = có điểm), st: [B, K] đặc trưng tĩnh.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# ----------------------------------------------------------------------------- KAN
class KANLinear(nn.Module):
    """Lớp KAN dạng B-spline (rút gọn theo efficient-kan): y = W_b·silu(x) + Σ spline(x)."""

    def __init__(self, in_f, out_f, grid_size=5, order=3, grid_range=(-3.0, 3.0)):
        super().__init__()
        self.order = order
        h = (grid_range[1] - grid_range[0]) / grid_size
        grid = torch.arange(-order, grid_size + order + 1, dtype=torch.float32) * h + grid_range[0]
        self.register_buffer("grid", grid)
        self.base = nn.Linear(in_f, out_f)
        self.spline_weight = nn.Parameter(torch.randn(out_f, in_f, grid_size + order) * 0.1 / grid_size)

    def b_splines(self, x):
        return b_splines(x, self.grid, self.order)

    def forward(self, x):
        shape = x.shape
        x = x.reshape(-1, shape[-1])
        out = self.base(F.silu(x)) + torch.einsum("nig,oig->no", self.b_splines(x), self.spline_weight)
        return out.reshape(*shape[:-1], -1)


def b_splines(x, grid, order):
    """x [..., F] -> cơ sở B-spline [..., F, G + order] (đệ quy Cox–de Boor)."""
    x = x.unsqueeze(-1)
    bases = ((x >= grid[:-1]) & (x < grid[1:])).to(x.dtype)
    for k in range(1, order + 1):
        bases = (x - grid[:-(k + 1)]) / (grid[k:-1] - grid[:-(k + 1)]) * bases[..., :-1] + \
                (grid[k + 1:] - x) / (grid[k + 1:] - grid[1:-k]) * bases[..., 1:]
    return bases


class KANEmbed(nn.Module):
    """Token hóa bằng KAN (theo TabKANet): mỗi đặc trưng số có một hàm spline riêng φ_s: R -> R^d."""

    def __init__(self, n_feat, d, grid_size=5, order=3, grid_range=(-3.0, 3.0)):
        super().__init__()
        self.order = order
        h = (grid_range[1] - grid_range[0]) / grid_size
        self.register_buffer("grid", torch.arange(-order, grid_size + order + 1, dtype=torch.float32) * h + grid_range[0])
        self.base_w = nn.Parameter(torch.randn(n_feat, d) * 0.3)
        self.bias = nn.Parameter(torch.zeros(n_feat, d))
        self.spline_w = nn.Parameter(torch.randn(n_feat, d, grid_size + order) * 0.1)

    def forward(self, x):  # [B, F] -> [B, F, d]
        sp = torch.einsum("bfg,fdg->bfd", b_splines(x, self.grid, self.order), self.spline_w)
        return F.silu(x).unsqueeze(-1) * self.base_w + sp + self.bias


class LinearEmbed(nn.Module):
    """Token hóa tuyến tính kiểu FT-Transformer: e = x·w_s + b_s."""

    def __init__(self, n_feat, d):
        super().__init__()
        self.w = nn.Parameter(torch.randn(n_feat, d) * 0.3)
        self.b = nn.Parameter(torch.zeros(n_feat, d))

    def forward(self, x):
        return x.unsqueeze(-1) * self.w + self.b


class GroupRational(nn.Module):
    """Hàm kích hoạt hữu tỉ an toàn theo nhóm của GR-KAN (KAT): P(x) / (1 + |Q(x)|)."""

    def __init__(self, dim, groups=4):
        super().__init__()
        assert dim % groups == 0
        self.groups = groups
        self.a = nn.Parameter(torch.tensor([0.0, 1.0, 0.2, 0.0, 0.0, 0.0]).repeat(groups, 1))
        self.b = nn.Parameter(torch.tensor([0.0, 0.1, 0.0, 0.0]).repeat(groups, 1))

    def forward(self, x):
        shape = x.shape
        x = x.reshape(*shape[:-1], self.groups, -1)
        a, b = self.a.unsqueeze(-1), self.b.unsqueeze(-1)
        num = a[:, 0] + x * (a[:, 1] + x * (a[:, 2] + x * (a[:, 3] + x * (a[:, 4] + x * a[:, 5]))))
        den = 1 + (x * (b[:, 0] + x * (b[:, 1] + x * (b[:, 2] + x * b[:, 3])))).abs()
        return (num / den).reshape(shape)


class GRKAN(nn.Module):
    """Khối GR-KAN thay cho mạng truyền thẳng của Transformer."""

    def __init__(self, d, hidden, dropout=0.1):
        super().__init__()
        self.act1, self.fc1 = GroupRational(d), nn.Linear(d, hidden)
        self.act2, self.fc2 = GroupRational(hidden), nn.Linear(hidden, d)
        self.drop = nn.Dropout(dropout)

    def forward(self, x):
        return self.fc2(self.drop(self.act2(self.fc1(self.act1(x)))))


def mlp_ffn(d, hidden, dropout=0.1):
    return nn.Sequential(nn.Linear(d, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, d))


# ----------------------------------------------------------------------------- tiện ích chung
def flat(xs, m, st):
    return torch.cat([xs.flatten(1), m.flatten(1), st], dim=1)


class Heads(nn.Module):
    def __init__(self, d, n_targets, n_classes, kan=False):
        super().__init__()
        self.reg = KANLinear(d, n_targets) if kan else nn.Linear(d, n_targets)
        self.cls = nn.Linear(d, n_classes)

    def forward(self, h):
        return self.reg(h), self.cls(h)


class FeatureTokens(nn.Module):
    """Biến (xs, m, st) thành chuỗi token đặc trưng [B, S*T + K, d]; ô khuyết dùng token mặt nạ học được."""

    def __init__(self, S, T, K, d, kan=False):
        super().__init__()
        emb = KANEmbed if kan else LinearEmbed
        self.cell, self.static = emb(S * T, d), emb(K, d)
        self.mask_tok = nn.Parameter(torch.zeros(S * T, d))

    def forward(self, xs, m, st):
        mm = m.flatten(1).unsqueeze(-1)
        cell = self.cell(xs.flatten(1)) * mm + self.mask_tok * (1 - mm)
        return torch.cat([cell, self.static(st)], dim=1)


# ----------------------------------------------------------------------------- mô hình so sánh
class MLP(nn.Module):
    def __init__(self, S, T, K, n_targets, n_classes, d=64, dropout=0.1, **_):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(2 * S * T + K, d), nn.ReLU(), nn.Dropout(dropout),
                                  nn.Linear(d, d), nn.ReLU(), nn.Dropout(dropout))
        self.heads = Heads(d, n_targets, n_classes)

    def forward(self, xs, m, st):
        return self.heads(self.body(flat(xs, m, st)))


class BiLSTM(nn.Module):
    """Bi-LSTM đọc chuỗi token đặc trưng (khi có nhiều học kỳ, chuỗi chạy theo môn × học kỳ)."""

    def __init__(self, S, T, K, n_targets, n_classes, d=32, dropout=0.1, **_):
        super().__init__()
        self.tok = FeatureTokens(S, T, K, d)
        self.lstm = nn.LSTM(d, d, batch_first=True, bidirectional=True)
        self.drop = nn.Dropout(dropout)
        self.heads = Heads(2 * d, n_targets, n_classes)

    def forward(self, xs, m, st):
        _, (h, _) = self.lstm(self.tok(xs, m, st))
        return self.heads(self.drop(torch.cat([h[0], h[1]], dim=1)))


class FTTransformer(nn.Module):
    def __init__(self, S, T, K, n_targets, n_classes, d=32, layers=2, heads=4, dropout=0.1, kan_embed=False, **_):
        super().__init__()
        self.tok = FeatureTokens(S, T, K, d, kan=kan_embed)
        self.cls = nn.Parameter(torch.zeros(1, 1, d))
        layer = nn.TransformerEncoderLayer(d, heads, 2 * d, dropout, batch_first=True, norm_first=True, activation="gelu")
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.heads = Heads(d, n_targets, n_classes)

    def forward(self, xs, m, st):
        t = self.tok(xs, m, st)
        t = self.enc(torch.cat([self.cls.expand(len(t), -1, -1), t], dim=1))
        return self.heads(self.norm(t[:, 0]))


class TabKANet(FTTransformer):
    """TabKANet: nhúng đặc trưng số bằng KAN rồi đưa vào Transformer chuẩn."""

    def __init__(self, *a, **kw):
        kw["kan_embed"] = True
        super().__init__(*a, **kw)


class Kanformer(nn.Module):
    """Mô hình kiểu Kanformer: multi-head attention trên token đặc trưng, sau đó là các lớp KAN."""

    def __init__(self, S, T, K, n_targets, n_classes, d=32, heads=4, dropout=0.1, **_):
        super().__init__()
        self.tok = FeatureTokens(S, T, K, d)
        self.attn = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(d)
        self.kan = KANLinear(d, d)
        self.drop = nn.Dropout(dropout)
        self.heads = Heads(d, n_targets, n_classes, kan=True)

    def forward(self, xs, m, st):
        t = self.tok(xs, m, st)
        t = self.norm(t + self.attn(t, t, t, need_weights=False)[0])
        return self.heads(self.drop(torch.tanh(self.kan(t.mean(1)))))


# ----------------------------------------------------------------------------- mô hình đề xuất
class AxialBlock(nn.Module):
    def __init__(self, d, heads, dropout, grkan=True, subject_attn=True):
        super().__init__()
        self.subject_attn = subject_attn
        self.n_t, self.attn_t = nn.LayerNorm(d), nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.n_s, self.attn_s = nn.LayerNorm(d), nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.n_f = nn.LayerNorm(d)
        self.ffn = GRKAN(d, 2 * d, dropout) if grkan else mlp_ffn(d, 2 * d, dropout)

    def forward(self, x):  # [B, S, T, d]
        B, S, T, d = x.shape
        if T > 1:  # chú ý theo trục thời gian (cùng môn, qua các học kỳ) với mặt nạ nhân quả
            h = self.n_t(x).reshape(B * S, T, d)
            causal = torch.triu(torch.ones(T, T, dtype=torch.bool, device=x.device), 1)
            x = x + self.attn_t(h, h, h, attn_mask=causal, need_weights=False)[0].reshape(B, S, T, d)
        if self.subject_attn:  # chú ý theo trục môn học (các môn trong cùng học kỳ)
            h = self.n_s(x).transpose(1, 2).reshape(B * T, S, d)
            a = self.attn_s(h, h, h, need_weights=False)[0]
            x = x + a.reshape(B, T, S, d).transpose(1, 2)
        return x + self.ffn(self.n_f(x))


class XEduKANFormer(nn.Module):
    """XEdu-KANFormer: token hóa KAN + Axial Transformer lai GR-KAN + đầu ra đa nhiệm.

    Các cờ kan_embed / grkan / subject_attn dùng cho nghiên cứu loại bỏ thành phần.
    """

    def __init__(self, S, T, K, n_targets, n_classes, d=32, layers=2, heads=4, dropout=0.1,
                 kan_embed=True, grkan=True, subject_attn=True, **_):
        super().__init__()
        self.S, self.T = S, T
        emb = KANEmbed if kan_embed else LinearEmbed
        self.cell = emb(S, d)                      # φ_KAN theo từng môn, dùng chung cho mọi học kỳ
        self.e_subj = nn.Parameter(torch.randn(S, 1, d) * 0.02)
        self.e_term = nn.Parameter(torch.randn(1, T, d) * 0.02)
        self.mask_tok = nn.Parameter(torch.zeros(d))
        self.static = emb(K, d)
        self.blocks = nn.ModuleList(AxialBlock(d, heads, dropout, grkan, subject_attn) for _ in range(layers))
        self.cls = nn.Parameter(torch.zeros(1, 1, d))
        self.read = nn.MultiheadAttention(d, heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(d)
        self.heads = Heads(d, n_targets, n_classes, kan=grkan)
        self.last_attn = None

    def forward(self, xs, m, st):
        B = len(xs)
        e = torch.stack([self.cell(xs[:, :, t]) for t in range(self.T)], dim=2)      # [B, S, T, d]
        mm = m.unsqueeze(-1)
        x = e * mm + self.mask_tok * (1 - mm) + self.e_subj + self.e_term.unsqueeze(1)
        for blk in self.blocks:
            x = blk(x)
        tokens = torch.cat([x.reshape(B, self.S * self.T, -1), self.static(st)], dim=1)
        h, w = self.read(self.cls.expand(B, -1, -1), tokens, tokens, need_weights=True)   # [CLS] đọc toàn lưới
        self.last_attn = w.detach().squeeze(1)
        return self.heads(self.norm(h.squeeze(1)))


TORCH_MODELS = {
    "MLP": (MLP, {}),
    "Bi-LSTM": (BiLSTM, {}),
    "FT-Transformer": (FTTransformer, {}),
    "TabKANet": (TabKANet, {}),
    "Kanformer": (Kanformer, {}),
    "XEdu-KANFormer": (XEduKANFormer, {}),
}
ABLATIONS = {
    "XEdu (bỏ chú ý liên môn)": (XEduKANFormer, {"subject_attn": False}),
    "XEdu (GR-KAN → MLP)": (XEduKANFormer, {"grkan": False}),
    "XEdu (bỏ token hóa KAN)": (XEduKANFormer, {"kan_embed": False}),
    "XEdu (bỏ đa nhiệm)": (XEduKANFormer, {"lam": 0.0}),
    "XEdu (nhỏ: d=16, 1 khối, dropout 0.2)": (XEduKANFormer, {"d": 16, "layers": 1, "dropout": 0.2}),
}
