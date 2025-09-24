## Removed deprecated/unused Session import to avoid ImportError

def init_arize_tracing():
    try:
        # Register OpenTelemetry and instrument LangChain for Phoenix
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor
        import os

        project_name = os.getenv("PHOENIX_PROJECT_NAME", "nepal-manifesto-chatbot")
        tracer_provider = register(project_name=project_name, auto_instrument=True)
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        print("✅ Phoenix tracing enabled.")
    except Exception as e:
        # Keep it non-blocking
        print(f"⚠️ Phoenix tracing not enabled: {e}")


