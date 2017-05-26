# coding=utf-8
# 统一的设置服务器端信息
import default_settings as dfs


class ServerSetting(dict):

    def __init__(self, names=(), values=(), **kw):
        super(ServerSetting, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        if key not in dir(self):
            raise AttributeError('No such key: %s' % key)
        return self.key


def merge(defconfig, overrideconfig):
    r = {}
    for k, v in defconfig.items():
        if k in overrideconfig:
            if isinstance(v, dict):
                r[k] = merge(v, overrideconfig[k])
            else:
                r[k] = overrideconfig[k]
        else:
            r[k] = v
    return r


def toInfo(dic):
    U = ServerSetting()
    for k, v in dic.items():
        U[k] = toInfo(v) if isinstance(v, dict) else v
    return U


configs = dfs.configs
try:
    import override_settings as ors
    configs = merge(configs, ors.configs)
except ImportError:
    pass
configs = toInfo(configs)
a = 55