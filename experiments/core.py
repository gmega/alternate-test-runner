import functools
import traceback
from dataclasses import dataclass
from logging import getLogger
from time import time
from typing import Callable, TypeVar, Generic, Union, Iterable, Iterator

T = TypeVar('T')

logger = getLogger(__name__)


@dataclass
class StageResult(Generic[T]):
    name: str
    info: str
    result: Union[T, Exception]
    time: float


def stage(fun: Callable[..., T]) -> Callable[..., StageResult[T]]:
    """Measure the time it takes to run a function."""

    @functools.wraps(fun)
    def wrapper(*args, **kwargs) -> StageResult[T]:
        info = kwargs.pop('_info') if '_info' in kwargs else ''
        start = time()
        try:
            logstr = f'{fun.__name__}' + (f' -- <<{info}>>' if info else '')
            logger.info(f'RUNNING {logstr}')
            result = fun(*args, **kwargs)
            logger.info(f'COMPLETED {logstr}')
        except Exception as e:
            traceback.print_exc()
            result = e
        return StageResult(result=result, time=time() - start, name=fun.__name__, info=info)

    wrapper.fn = fun

    return wrapper


StageIterator = Iterator[StageResult]


class Experiment:
    def __init__(self, stages: StageIterator, experiment_id: str):
        self.stages = stages
        self.experiment_id = experiment_id

    def run(self):
        for a_stage in self.stages:
            if isinstance(a_stage.result, Exception):
                logger.error(f'Error: {a_stage.result}')
            else:
                logger.info(f'{self.experiment_id},{a_stage.name},{a_stage.time:.2f},"{a_stage.info}"')


ExperimentFun = Callable[..., StageIterator]


def experiment(fun: ExperimentFun) -> Callable[..., Experiment]:
    @functools.wraps(fun)
    def wrapper(*args, **kwargs) -> Experiment:
        experiment_id = kwargs.pop('experiment_id')
        return Experiment(stages=fun(*args, **kwargs), experiment_id=experiment_id)

    return wrapper
