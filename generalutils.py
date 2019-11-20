import time

def timeit(method):
    def timed(*args, **kw):
        start_time = time.perf_counter()
        result = method(*args, **kw)
        end_time = time.perf_counter()
        run_time = end_time - start_time

        print(f"\nFinished {method.__name__!r} in {run_time:.4f} secs")
        return result
    return timed
