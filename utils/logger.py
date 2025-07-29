import logging, json, sys, time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": time.time(),
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        if record.exc_info:
            base["exc"] = self.formatException(record.exc_info)
        return json.dumps(base)


def setup_logger() -> logging.Logger:
    root = logging.getLogger()
    if root.handlers:
        return root
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    return root


log = setup_logger()
