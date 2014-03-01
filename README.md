Struct-o-Miner
==============

Python package for extracting structured data from XML/HTML documents

**Work in (frantic) progress**.

Examples can be found in the [examples](https://github.com/aGHz/structominer/tree/master/examples) directory. To run them while waiting for proper python packaging:

    # install libxml2 using your native package manager
    git clone https://github.com/aGHz/structominer.git structominer
    cd structominer
    virtualenv --distribute --no-site-packages .
    . bin/activate
    pip install lxml requests
    PYTHONPATH="../" python examples/hn.py
