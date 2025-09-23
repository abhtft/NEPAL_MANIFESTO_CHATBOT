openai.NotFoundError: Error code: 404 - {'error': {'code': '404', 'message': 'Resource not found'}}
Traceback:
File "/app/app.py", line 31, in <module>
    result = chain.invoke({"question": query})
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 165, in invoke
    self._call(inputs, run_manager=run_manager)
File "/usr/local/lib/python3.11/site-packages/langchain/chains/conversational_retrieval/base.py", line 175, in _call
    answer = self.combine_docs_chain.run(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_core/_api/deprecation.py", line 193, in warning_emitting_wrapper
    return wrapped(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 632, in run
    return self(kwargs, callbacks=callbacks, tags=tags, metadata=metadata)[
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_core/_api/deprecation.py", line 193, in warning_emitting_wrapper
    return wrapped(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 410, in __call__
    return self.invoke(
           ^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 165, in invoke
    self._call(inputs, run_manager=run_manager)
File "/usr/local/lib/python3.11/site-packages/langchain/chains/combine_documents/base.py", line 143, in _call
    output, extra_return_dict = self.combine_docs(
                                ^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/combine_documents/stuff.py", line 263, in combine_docs
    return self.llm_chain.predict(callbacks=callbacks, **inputs), {}
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/llm.py", line 325, in predict
    return self(kwargs, callbacks=callbacks)[self.output_key]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_core/_api/deprecation.py", line 193, in warning_emitting_wrapper
    return wrapped(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 410, in __call__
    return self.invoke(
           ^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/base.py", line 165, in invoke
    self._call(inputs, run_manager=run_manager)
File "/usr/local/lib/python3.11/site-packages/langchain/chains/llm.py", line 127, in _call
    response = self.generate([inputs], run_manager=run_manager)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain/chains/llm.py", line 139, in generate
    return self.llm.generate_prompt(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 1023, in generate_prompt
    return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 840, in generate
    self._generate_with_cache(
File "/usr/local/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 1089, in _generate_with_cache
    result = self._generate(
             ^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/langchain_openai/chat_models/base.py", line 1184, in _generate
    raise e
File "/usr/local/lib/python3.11/site-packages/langchain_openai/chat_models/base.py", line 1179, in _generate
    raw_response = self.client.with_raw_response.create(**payload)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/openai/_legacy_response.py", line 364, in wrapped
    return cast(LegacyAPIResponse[R], func(*args, **kwargs))
                                      ^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/openai/_utils/_utils.py", line 286, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/openai/resources/chat/completions/completions.py", line 1147, in create
    return self._post(
           ^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/openai/_base_client.py", line 1259, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/openai/_base_client.py", line 1047, in request
    raise self._make_status_error_from_response(err.response) from None