import functools
from typing import Optional

from . import chainable as C
from . import utils


class ForeachAdamW(C.BaseOpt):
    def __init__(self, params, lr=0.0025, betas=(0.9, 0.99), eps=1e-8, weight_decay=0, warmup_steps=0,
                 foreach: bool = True, storage_dtype: str = 'float32', mars: bool = False, caution: bool = False,
                 mars_gamma: float = 0.0025, gradient_clipping: C.str_or_fn = C.use_default,
                 update_clipping: C.str_or_fn = C.use_default, palm: bool = C.use_default, beta2_scale: float = 0.8):
        defaults = dict(lr=lr, betas=betas, eps=eps, k=0, warmup_steps=warmup_steps, train_mode=True, weight_sum=0.0,
                        lr_max=-1.0, weight_decay=weight_decay, storage_dtype=storage_dtype, mars=mars, caution=caution,
                        mars_gamma=mars_gamma, beta2_scale=beta2_scale)
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm, C.update_by_adam)


class ForeachRMSprop(C.BaseOpt):
    """
    Debiased RMSprop (not torch.optim.RMSprop)
    """

    def __init__(self, params, lr=0.0025, betas=(0.9, 0.99), eps=1e-6, weight_decay=0, warmup_steps=0, r=0.0,
                 weight_lr_power=2.0, foreach: bool = True, storage_dtype: str = 'float32', mars: bool = False,
                 caution: bool = False, mars_gamma: float = 0.0025, gradient_clipping: C.str_or_fn = C.use_default,
                 update_clipping: C.str_or_fn = C.use_default, palm: bool = C.use_default, beta2_scale: float = 0.8):
        defaults = dict(lr=lr, betas=betas, eps=eps, warmup_steps=warmup_steps, weight_decay=weight_decay,
                        foreach=foreach, storage_dtype=storage_dtype, mars=mars, caution=caution, mars_gamma=mars_gamma,
                        beta2_scale=beta2_scale)
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm, C.scale_by_exp_avg_sq)


class ForeachSFAdamW(C.ScheduleFree):
    def __init__(self, params, lr=0.0025, betas=(0.9, 0.99), eps=1e-6, weight_decay=0, warmup_steps=0, r=0.0,
                 weight_lr_power=2.0, foreach: bool = True, storage_dtype: str = 'float32', mars: bool = False,
                 caution: bool = False, mars_gamma: float = 0.0025, gradient_clipping: C.str_or_fn = C.use_default,
                 update_clipping: C.str_or_fn = C.use_default, palm: bool = C.use_default, beta2_scale: float = 0.8):
        defaults = dict(lr=lr, betas=betas, eps=eps, r=r, k=0, warmup_steps=warmup_steps, train_mode=True,
                        weight_sum=0.0, lr_max=-1.0, weight_lr_power=weight_lr_power, weight_decay=weight_decay,
                        foreach=foreach, storage_dtype=storage_dtype, mars=mars, caution=caution, mars_gamma=mars_gamma,
                        beta2_scale=beta2_scale)
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm, C.scale_by_exp_avg_sq,
                         C.update_by_schedule_free)


class PaLMForeachSFAdamW(ForeachSFAdamW):
    palm: bool = True


class ForeachADOPT(C.BaseOpt):
    def __init__(self, params, lr=0.0025, betas=(0.9, 0.99), eps=1e-8, weight_decay=0, warmup_steps=0,
                 foreach: bool = True, storage_dtype: str = 'float32', mars: bool = False, caution: bool = False,
                 mars_gamma: float = 0.0025, gradient_clipping: C.str_or_fn = C.use_default,
                 update_clipping: C.str_or_fn = C.use_default, palm: bool = C.use_default, beta2_scale: float = 0.8):
        defaults = dict(lr=lr, betas=betas, eps=eps, k=0, warmup_steps=warmup_steps, train_mode=True, weight_sum=0.0,
                        lr_max=-1.0, weight_decay=weight_decay, storage_dtype=storage_dtype, mars=mars, caution=caution,
                        mars_gamma=mars_gamma, beta2_scale=beta2_scale)
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm, C.update_by_adopt)


class ForeachLaProp(C.BaseOpt):
    def __init__(self, params, lr=0.0025, betas=(0.9, 0.99), eps=1e-8, weight_decay=0, warmup_steps=0,
                 foreach: bool = True, storage_dtype: str = 'float32', mars: bool = False, caution: bool = False,
                 mars_gamma: float = 0.0025, gradient_clipping: C.str_or_fn = C.use_default,
                 update_clipping: C.str_or_fn = C.use_default, palm: bool = C.use_default, beta2_scale: float = 0.8):
        defaults = dict(lr=lr, betas=betas, eps=eps, k=0, warmup_steps=warmup_steps, train_mode=True, weight_sum=0.0,
                        lr_max=-1.0, weight_decay=weight_decay, storage_dtype=storage_dtype, mars=mars, caution=caution,
                        mars_gamma=mars_gamma, beta2_scale=beta2_scale)
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm, C.update_by_laprop)


class ForeachSOAP(C.BaseOpt):
    """
    ForeachSOAP

    Sources:
        Baseline SOAP:
            SOAP: Improving and Stabilizing Shampoo using Adam
            Nikhil Vyas, Depen Morwani, Rosie Zhao, Itai Shapira, David Brandfonbrener, Lucas Janson, Sham Kakade
            https://arxiv.org/abs/2409.11321
            https://github.com/nikhilvyas/SOAP

        ScheduleFree:
            The Road Less Scheduled
            Aaron Defazio, Xingyu Alice Yang, Harsh Mehta, Konstantin Mishchenko, Ahmed Khaled, Ashok Cutkosky
            https://arxiv.org/abs/2405.15682
            https://github.com/facebookresearch/schedule_free
    """
    use_precond_schedule: bool = False

    def __init__(self, params, lr: float = 3e-3, betas=(0.9, 0.95), shampoo_beta: float = 0.95, eps: float = 1e-8,
                 weight_decay: float = 0.01, precondition_frequency: int = 2, max_precond_dim: int = 2048,  #
                 merge_dims: bool = True, precondition_1d: bool = False, normalize_grads: bool = False,
                 data_format: str = "channels_first", correct_bias: bool = True, warmup_steps: int = 1,
                 split: bool = False, foreach: bool = True, mars: bool = False, caution: bool = False,
                 mars_gamma: float = 0.0025, palm: bool = C.use_default, precond_scheduler=(1 / 3, 9),
                 beta2_scale: float = 0.8, use_precond_schedule: bool = C.use_default,
                 gradient_clipping: C.str_or_fn = C.use_default, update_clipping: C.str_or_fn = C.use_default):
        use_precond_schedule = C.default(use_precond_schedule, self.use_precond_schedule)

        defaults = {"lr": lr, "betas": betas, "shampoo_beta": shampoo_beta, "eps": eps, "weight_decay": weight_decay,
                    "precondition_frequency": precondition_frequency, "max_precond_dim": max_precond_dim,
                    "merge_dims": merge_dims, "precondition_1d": precondition_1d, "normalize_grads": normalize_grads,
                    "correct_bias": correct_bias, 'warmup_steps': warmup_steps, 'split': split, 'mars': mars,
                    'caution': caution, 'mars_gamma': mars_gamma, 'palm': palm, 'precond_scheduler': precond_scheduler,
                    'beta2_scale': beta2_scale}
        if use_precond_schedule:
            del defaults['precondition_frequency']
        else:
            del defaults['precond_scheduler']
        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, palm,  #
                         C.scale_by_soap)


class PaLMForeachSOAP(ForeachSOAP):
    use_precond_schedule: bool = False
    palm: bool = True


class PrecondScheduleForeachSOAP(ForeachSOAP):
    use_precond_schedule: bool = True


class PrecondSchedulePaLMForeachSOAP(ForeachSOAP):
    use_precond_schedule: bool = True
    palm: bool = True


class ForeachPSGDKron(C.BaseOpt):
    """
    Originally from Evan Walters and Omead Pooladzandi, 2024
    Modified under Creative Commons Attribution 4.0 International
    Source available at https://github.com/evanatyourservice/kron_torch/blob/97a2b5ee8a1a4c29e4780bbf6c521e545189eff9/kron_torch/kron.py
    """

    delayed: bool = False
    cached: bool = False
    exp_avg_input: bool = True

    def __init__(self, params, lr=0.001, beta=0.9, weight_decay=0.0, preconditioner_update_probability=None,
                 max_size_triangular=2048, min_ndim_triangular=2, memory_save_mode=None,
                 momentum_into_precond_update=True, warmup_steps: int = 1, merge_dims: bool = False,
                 split: bool = False, store_triu_as_line: bool = True, foreach: bool = True, q_dtype='float32',
                 stochastic_schedule: bool = True, storage_dtype: str = 'float32', mars: bool = False,
                 caution: bool = False, mars_gamma: float = 0.0025, delayed: Optional[bool] = C.use_default,
                 cached: Optional[bool] = C.use_default, exp_avg_input: Optional[bool] = C.use_default,
                 gradient_clipping: C.str_or_fn = C.use_default, update_clipping: C.str_or_fn = C.use_default,  #
                 # expert parameters
                 precond_init_scale=1.0, precond_lr=0.1):
        delayed = C.default(delayed, self.delayed)
        cached = C.default(cached, self.cached)
        exp_avg_input = C.default(exp_avg_input, self.exp_avg_input)
        update_clipping = C.default(update_clipping, utils.trust_region_clip_)

        defaults = dict(lr=lr, beta=beta, weight_decay=weight_decay, max_size_triangular=max_size_triangular,
                        min_ndim_triangular=min_ndim_triangular, memory_save_mode=memory_save_mode,
                        momentum_into_precond_update=momentum_into_precond_update, precond_lr=precond_lr,
                        precond_init_scale=precond_init_scale, step=0, warmup_steps=warmup_steps, merge_dims=merge_dims,
                        split=split, store_triu_as_line=store_triu_as_line, q_dtype=q_dtype,
                        storage_dtype=storage_dtype, caution=caution, mars_gamma=mars_gamma, mars=mars,
                        stochastic_schedule=stochastic_schedule)

        super().__init__(params, defaults, foreach, gradient_clipping, update_clipping, False,  #
                         *(C.exp_avg,) * exp_avg_input,  #
                         functools.partial(C.scale_by_delayed_psgd if delayed else C.scale_by_psgd, cached=cached,
                                           prob=preconditioner_update_probability))


class ForeachPurePSGD(ForeachPSGDKron):
    exp_avg_input: bool = False


class ForeachCachedDelayedPSGDKron(ForeachPSGDKron):
    delayed: bool = True
    cached: bool = True


class ForeachCachedPSGDKron(ForeachPSGDKron):
    cached: bool = True


class ForeachDelayedPSGD(ForeachPSGDKron):
    delayed: bool = True


PalmForEachSoap = PaLMForeachSOAP
PaLMSOAP = PaLMForeachSOAP
PaLMSFAdamW = PaLMForeachSFAdamW
SOAP = ForeachSOAP
SFAdamW = ForeachSFAdamW
LaProp = ForeachLaProp
ADOPT = ForeachADOPT
RMSprop = ForeachRMSprop
PrecondScheduleSOAP = PrecondScheduleForeachSOAP
PrecondSchedulePaLMSOAP = PrecondSchedulePaLMForeachSOAP
PSGDKron = ForeachPSGDKron
AdamW = ForeachAdamW
PurePSGD = ForeachPurePSGD
DelayedPSGD = ForeachDelayedPSGD
CachedPSGDKron = ForeachCachedPSGDKron
CachedDelayedPSGDKron = ForeachCachedDelayedPSGDKron

__all__ = ["PrecondSchedulePaLMSOAP", "PSGDKron", "PurePSGD", "DelayedPSGD", "CachedPSGDKron", "CachedDelayedPSGDKron",
           "PalmForEachSoap", "PaLMSOAP", "PaLMSFAdamW", "LaProp", "ADOPT", "PrecondScheduleSOAP",
           "PrecondSchedulePaLMSOAP", 'RMSprop',  #
           "ForeachAdamW", "ForeachSFAdamW", "ForeachLaProp", "ForeachADOPT", "ForeachSOAP", "ForeachPSGDKron",
           "ForeachPurePSGD", "ForeachDelayedPSGD", "ForeachCachedPSGDKron", "ForeachCachedDelayedPSGDKron",
           "ForeachRMSprop"]
