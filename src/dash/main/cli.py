import click


def enable_debugpy():
    import debugpy  # noqa: T100

    debugpy.listen(("0.0.0.0", 5678))  # noqa: S104, T100


def enable_datadog():
    import ddtrace.auto  # noqa: F401
    import ddtrace.profiling.auto  # noqa: F401


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    from .config import Config

    config = Config()
    ctx.obj = {"config": config}

    if config.app.enable_datadog:
        enable_datadog()

    from .logging.setup import configure_logging

    configure_logging(
        level=config.logging.level,
        json_logs=config.logging.json_mode,
        colorize=config.logging.colorize,
    )

    if config.app.enable_debugpy:
        enable_debugpy()


@cli.command()
@click.pass_context
def run(ctx: click.Context):
    import uvicorn

    from dash.main.app import get_app

    from .config import Config

    config: Config = ctx.obj["config"]

    uvicorn.run(
        get_app(),
        host=config.app.host,
        port=config.app.port,
        loop="uvloop",
        proxy_headers=config.app.proxy_headers,
        forwarded_allow_ips=config.app.forwarded_allow_ips,
        access_log=False,
        log_config=None,
    )
