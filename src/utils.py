from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    return Path(__file__).parent.parent


def json_value(data, *args, default=None):
    cur = data
    for a in args:
        try:
            if isinstance(a, int):
                cur = cur[a]
            else:
                cur = cur.get(a)
        except (IndexError, KeyError, TypeError, AttributeError):
            return default
    return cur

def repetitive_polling(func_main, func_check=lambda x: x, func_post_check=lambda: print(),
                       init_step=1, max_step=3600, step_increase_rate=2, step_increase_cycle=5, infinite=True):
    is_updated = False
    step = init_step
    while True:
        try:
            print('polling :', step)
            is_updated = func_check(
                polling2.poll(func_main,
                              check_success=func_check,
                              step=step,
                              timeout=step * (step_increase_cycle) - 1)
            )

            func_post_check()

            # 대기시간 초기화
            step = init_step

        except Exception:
            # 대기시간 증가
            step = min(step * step_increase_rate, max_step)
            print("step increased to", step, datetime.now())

        if not infinite and step == max_step:
            print("exit polling")
            return is_updated



if __name__ == "__main__":
    pass
