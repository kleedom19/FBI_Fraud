<h1>What we have done</h1>

I have the model code from HuggingFace's website loaded with 2 images from the PDF we want to analyze, and then the Modal endpoint code that Jacob made. 
I did discover that no actual app or token was created, so I went ahead and created this on my Modal account and connected it through VS Code via terminal.
The idea is for Modal to use our local files 'deepseekOcr.py', which as the modal code in it, and 'ocr_endpoint.py', which has the FastAPI app that Jacob made, and use
them in deployment. I have seen videos of the demo, and it looks like it should load a screen that allows you to put pdf's in? 
<br>
I understand a few of the errors saying that I have to change a few of the commands to more updated versions, but I don't understand the other chunk.
<br> 
My modal also keeps sending me emails saying that I have crashed it too many times, so it won't run function cells.


<h1>These are the current errors I am getting from Modal:</h1>


/root/deploy_modal.py:47: DeprecationError: 2025-02-24: We have renamed several parameters related to autoscaling. Please update your code to use the following new names:

- concurrency_limit -> max_containers

See https://modal.com/docs/guide/modal-1-0-migration for more details.
  @app.function(
Loaded tokens: ak-A****
Traceback (most recent call last):
  File "/pkg/modal/_runtime/container_io_manager.py", line 907, in handle_user_exception
    yield
  File "/pkg/modal/_container_entrypoint.py", line 502, in main
    finalized_functions = service.get_finalized_functions(function_def, container_io_manager)
  File "/pkg/modal/_runtime/user_code_imports.py", line 126, in get_finalized_functions
    web_callable, lifespan_manager = construct_webhook_callable(
  File "/pkg/modal/_runtime/user_code_imports.py", line 80, in construct_webhook_callable
    user_defined_callable()
  File "/root/deploy_modal.py", line 62, in run
    uvicorn.run("ocr_endpoint:app", host="0.0.0.0", port=8000)
  File "/usr/local/lib/python3.9/site-packages/uvicorn/main.py", line 593, in run
    server.run()
  File "/usr/local/lib/python3.9/site-packages/uvicorn/server.py", line 67, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
  File "/usr/local/lib/python3.9/site-packages/uvicorn/_compat.py", line 60, in asyncio_run
    return loop.run_until_complete(main)
  File "/usr/local/lib/python3.9/asyncio/base_events.py", line 647, in run_until_complete
    return future.result()
  File "/usr/local/lib/python3.9/site-packages/uvicorn/server.py", line 71, in serve
    await self._serve(sockets)
  File "/usr/local/lib/python3.9/site-packages/uvicorn/server.py", line 78, in _serve
    config.load()
  File "/usr/local/lib/python3.9/site-packages/uvicorn/config.py", line 439, in load
    self.loaded_app = import_from_string(self.app)
  File "/usr/local/lib/python3.9/site-packages/uvicorn/importer.py", line 22, in import_from_string
    raise exc from None
  File "/usr/local/lib/python3.9/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "/usr/local/lib/python3.9/importlib/__init__.py", line 127, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 680, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 850, in exec_module
  File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed
  File "/root/ocr_endpoint.py", line 7, in <module>

    from deepseekOcr import model, tokenizer
  File "/root/deepseekOcr.py", line 1, in <module>
    from vllm import LLM, SamplingParams
ModuleNotFoundError: No module named 'vllm'

Runner failed with exception: ModuleNotFoundError("No module named 'vllm'")


<h1> After updating a few of the errors</h1>
<h2> I ran it again and got an "Internal Server Error", so between that and Modal not reading functions at this time due to the crashing,
all I can provide is the log</h2>
<br>

🚀 Starting DeepSeek OCR endpoint...
Using token: ak-A****
Traceback (most recent call last):
  File "/pkg/modal/_runtime/container_io_manager.py", line 948, in handle_input_exception
    yield
  File "/pkg/modal/_container_entrypoint.py", line 208, in run_input_async
    async for value in gen:
  File "/pkg/modal/_runtime/container_io_manager.py", line 276, in call_generator_async
    async for result in gen:
  File "/pkg/modal/_runtime/asgi.py", line 227, in fn
    app_task.result()  # consume/raise exceptions if there are any!
  File "/usr/local/lib/python3.10/site-packages/fastapi/applications.py", line 1134, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/applications.py", line 113, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/usr/local/lib/python3.10/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.10/site-packages/starlette/middleware/cors.py", line 85, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.10/site-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/fastapi/routing.py", line 125, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/usr/local/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.10/site-packages/fastapi/routing.py", line 111, in app
    response = await f(request)
  File "/usr/local/lib/python3.10/site-packages/fastapi/routing.py", line 391, in app
    raw_response = await run_endpoint_function(
  File "/usr/local/lib/python3.10/site-packages/fastapi/routing.py", line 292, in run_endpoint_function
    return await run_in_threadpool(dependant.call, **values)
  File "/usr/local/lib/python3.10/site-packages/starlette/concurrency.py", line 38, in run_in_threadpool
    return await anyio.to_thread.run_sync(func)
  File "/usr/local/lib/python3.10/site-packages/anyio/to_thread.py", line 56, in run_sync
    return await get_async_backend().run_sync_in_worker_thread(
  File "/usr/local/lib/python3.10/site-packages/anyio/_backends/_asyncio.py", line 2485, in run_sync_in_worker_thread
    return await future
  File "/usr/local/lib/python3.10/site-packages/anyio/_backends/_asyncio.py", line 976, in run
    result = context.run(func, *args)
  File "/root/deploy_modal.py", line 80, in serve
    uvicorn.run(
  File "/usr/local/lib/python3.10/site-packages/uvicorn/main.py", line 593, in run
    server.run()
  File "/usr/local/lib/python3.10/site-packages/uvicorn/server.py", line 67, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
  File "/usr/local/lib/python3.10/site-packages/uvicorn/_compat.py", line 60, in asyncio_run
    return loop.run_until_complete(main)
  File "/usr/local/lib/python3.10/asyncio/base_events.py", line 649, in run_until_complete
    return future.result()
  File "/usr/local/lib/python3.10/site-packages/uvicorn/server.py", line 71, in serve
    await self._serve(sockets)
  File "/usr/local/lib/python3.10/site-packages/uvicorn/server.py", line 78, in _serve
    config.load()
  File "/usr/local/lib/python3.10/site-packages/uvicorn/config.py", line 439, in load
    self.loaded_app = import_from_string(self.app)
  File "/usr/local/lib/python3.10/site-packages/uvicorn/importer.py", line 22, in import_from_string
    raise exc from None
  File "/usr/local/lib/python3.10/site-packages/uvicorn/importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
  File "/usr/local/lib/python3.10/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1050, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1027, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1006, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 688, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 883, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/root/ocr_endpoint.py", line 7, in <module>
    from deepseekOcr import model, tokenizer
  File "/root/deepseekOcr.py", line 1, in <module>
    from vllm import LLM, SamplingParams
ModuleNotFoundError: No module named 'vllm'

    GET / -> 500 Internal Server Error  (duration: 148.5 ms, execution: 88.5 ms)
