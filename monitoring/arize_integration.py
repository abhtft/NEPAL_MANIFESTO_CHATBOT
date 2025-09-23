## Removed deprecated/unused Session import to avoid ImportError

def init_arize_tracing():
    try:
        # Register OpenTelemetry and instrument LangChain for Phoenix
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor

        tracer_provider = register(project_name="nepal-manifesto-chatbot", auto_instrument=True)
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        print("✅ Phoenix tracing enabled.")
    except Exception as e:
        # Keep it non-blocking
        print(f"⚠️ Phoenix tracing not enabled: {e}")
