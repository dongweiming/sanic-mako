# sanic-mako
Mako support for sanic

## Installation

`python3 -m pip install sanic-mako`

## Features

`sanic-mako` supports:

- `@jinja.template` syntax
- [session extension](https://github.com/subyraman/sanic_session) support
- factory pattern `init_app` method for creating apps

```python

from sanic import Sanic
from sanic_session import Session
from sanic_mako import SanicMako

app = Sanic()
Session(app)

mako = SanicMako(app)
# or setup later
# mako = SanicMako()
# mako.init_app(app)

@app.route('/')
@mako.template('index.html')  # decorator method is staticmethod
async def index(request):
    return {'greetings': 'Hello, sanic!'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```
