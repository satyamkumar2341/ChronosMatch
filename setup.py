
from setuptools import Extension, setup
from Cython.Build import cythonize

extensions = [
    Extension(
        name="src.fast_engine",
        sources=["src/fast_engine.pyx"],
    )
]

setup(
    name="chronosmatch",
    version="0.1.0",
    packages=["src"],
    ext_modules=cythonize(
        extensions,
        compiler_directives={"language_level": 3},
    ),
)
