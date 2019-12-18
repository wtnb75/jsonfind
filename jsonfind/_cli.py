from ._version import VERSION
import sys
import functools
import click
import json
from logging import getLogger, basicConfig, INFO, DEBUG
from .jsonfind import JsonFind, format_list, find_format_list, EQ, IS, IN1, IN2
from .jsonfind import compare_regexp, compare_regexp_substr, compare_eval, compare_fnmatch, compare_range

log = getLogger(__name__)


@click.group(invoke_without_command=True)
@click.version_option(VERSION)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


def set_verbose(flag):
    fmt = '%(asctime)s %(levelname)s %(message)s'
    if flag:
        basicConfig(level=DEBUG, format=fmt)
    else:
        basicConfig(level=INFO, format=fmt)


_common_option = [
    click.option("--verbose/--no-verbose", default=False),
    click.option("--target", type=str, required=True,
                 help="query(JSON string)"),
    click.option(
        "--format", type=click.Choice(format_list), default="jsonpointer"),
    click.argument("obj", type=click.File('r'), default=sys.stdin),
]


def common_option(decs):
    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f
    return deco


def obj_option(func):
    @functools.wraps(func)
    def wrap(verbose, obj, target, format, *args, **kwargs):
        set_verbose(verbose)
        objdata = json.load(obj)
        try:
            targetdata = json.loads(target)
        except json.decoder.JSONDecodeError:
            targetdata = target
        return func(verbose, objdata, targetdata, format, *args, **kwargs)
    return common_option(_common_option)(wrap)


@cli.command()
@click.option("--verbose/--no-verbose", default=False)
@click.option("--query", type=str, required=True, help="query string(jsonpointer or jsonpath)")
@click.option("--format", type=click.Choice(find_format_list), default="jsonpointer")
@click.argument("obj", type=click.File('r'), default=sys.stdin)
def find_by(verbose, obj, query, format):
    set_verbose(verbose)
    log.debug("finding(by) %s from %s (%s)", query, obj, format)
    res = JsonFind.find_by(mode=format, obj=json.load(obj), path=query)
    click.echo(json.dumps(res))


@cli.command()
@obj_option
def find_eq(verbose, obj, target, format):
    log.debug("finding(eq) %s from %s", target, obj)
    result = [JsonFind.format_to(format, x)
              for x in JsonFind.filter_eq(obj, target)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


@cli.command()
@obj_option
def find_is(verbose, obj, target, format):
    log.debug("finding(is) %s from %s", target, obj)
    result = [JsonFind.format_to(format, x)
              for x in JsonFind.filter_is(obj, target)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


@cli.command()
@obj_option
def find_subset(verbose, obj, target, format):
    log.debug("finding(subset) %s from %s", target, obj)
    result = [JsonFind.format_to(format, x)
              for x in JsonFind.filter_subset(obj, target)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


@cli.command()
@obj_option
def find_key(verbose, obj, target, format):
    log.debug("finding(subset) %s from %s", target, obj)
    result = [JsonFind.format_to(format, x)
              for x in JsonFind.filter_key(obj, target)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


@cli.command()
@obj_option
def find_regex(verbose, obj, target, format):
    log.debug("finding(regex val) %s from %s", target, obj)
    result = [JsonFind.format_to(format, x)
              for x in JsonFind.filter_compare(obj, target, EQ, compare_regexp)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


compare_fn = {
    "eq": EQ,
    "is": IS,
    "in1": IN1,
    "in2": IN2,
    "match": compare_regexp,
    "sub": compare_regexp_substr,
    "eval": compare_eval,
    "fnmatch": compare_fnmatch,
    "range": compare_range,
}

filter_fn = {
    "sub": JsonFind.filter_compare_subset,
    "super": JsonFind.filter_compare_superset,
    "set": JsonFind.filter_compare,
}


@cli.command()
@obj_option
@click.option("--key", type=click.Choice(compare_fn.keys()), default="eq")
@click.option("--value", type=click.Choice(compare_fn.keys()), default="eq")
@click.option("--mode", type=click.Choice(filter_fn.keys()), default="set")
def find_any(verbose, obj, target, format, key, value, mode):
    log.debug("finding(regex val) %s from %s (key=%s, value=%s, mode=%s)",
              target, obj, key, value, mode)
    key_fn = compare_fn.get(key)
    val_fn = compare_fn.get(value)
    cmpfn = filter_fn.get(mode)
    result = [JsonFind.format_to(format, x)
              for x in cmpfn(obj, target, key_fn, val_fn)]
    log.debug("result: %s", result)
    click.echo(json.dumps(result))


if __name__ == "__main__":
    cli()
