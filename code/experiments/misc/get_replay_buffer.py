import numpy as np
from gym.spaces.box import Box
from gym.spaces.discrete import Discrete
from cpprb import ReplayBuffer, PrioritizedReplayBuffer
from code.algos.policy_base import OffPolicyAgent


def is_discrete(space):
    if isinstance(space, Discrete):
        return True
    elif isinstance(space, Box):
        return False
    else:
        raise NotImplementedError


def get_space_size(space):
    if isinstance(space, Box):
        return space.shape
    elif isinstance(space, Discrete):
        return [1, ]  # space.n
    else:
        raise NotImplementedError("Assuming to use Box or Discrete, not {}".format(type(space)))


def get_default_rb_dict(size, env, observation_space):
    return {
        "size": size,
        "default_dtype": np.float32,
        "env_dict": {
            "obs": {
                "shape": observation_space},
            "next_obs": {
                "shape": observation_space},
            "act": {
                "shape": get_space_size(env.action_space)},
            "rew": {},
            "done": {}, 
            "mask": {}}}


def get_replay_buffer(policy, env, use_prioritized_rb=False,
                      use_nstep_rb=False, n_step=1, size=None,  
                      use_encode=False, use_absorbing_state=False):
    if policy is None or env is None:
        return None
    obs_shape = get_space_size(env.observation_space)
    if use_absorbing_state:
        obs_shape = (obs_shape[0] + 1, )
    kwargs = get_default_rb_dict(policy.memory_capacity, env, obs_shape)

    if size is not None:
        kwargs["size"] = size

    # on-policy policy
    if not issubclass(type(policy), OffPolicyAgent):
        kwargs["size"] = policy.horizon
        kwargs["env_dict"].pop("next_obs")
        kwargs["env_dict"].pop("rew")
        # TODO: Remove done. Currently cannot remove because of cpprb implementation
        # kwargs["env_dict"].pop("done")
        kwargs["env_dict"]["logp"] = {}
        kwargs["env_dict"]["ret"] = {}
        kwargs["env_dict"]["adv"] = {}
        if is_discrete(env.action_space):
            kwargs["env_dict"]["act"]["dtype"] = np.int32
        return ReplayBuffer(**kwargs)

    # N-step prioritized
    if use_prioritized_rb and use_nstep_rb:
        kwargs["Nstep"] = {"size": n_step,
                           "gamma": policy.discount,
                           "rew": "rew",
                           "next": "next_obs"}
        return PrioritizedReplayBuffer(**kwargs)

    if len(obs_shape) == 3:
        kwargs["env_dict"]["obs"]["dtype"] = np.ubyte
        kwargs["env_dict"]["next_obs"]["dtype"] = np.ubyte

    # prioritized
    if use_prioritized_rb:
        return PrioritizedReplayBuffer(**kwargs)

    # N-step
    if use_nstep_rb:
        kwargs["Nstep"] = {"size": n_step,
                           "gamma": policy.discount,
                           "rew": "rew",
                           "next": "next_obs"}
        return ReplayBuffer(**kwargs)
    
    if use_encode:
        kwargs["env_dict"]["encode"] = {}

    return ReplayBuffer(**kwargs)
