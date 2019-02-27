import math
import os
import random
import time

import click
from firebase_admin import firestore, initialize_app, credentials

all_colors = 'black', 'red', 'green', 'yellow', 'blue', 'magenta', \
             'cyan', 'white', 'bright_black', 'bright_red', \
             'bright_green', 'bright_yellow', 'bright_blue', \
             'bright_magenta', 'bright_cyan', 'bright_white'


@click.group()
def cli():
    """Firetore CLI tools

     This is
     a firestore tools.
    """
    click.echo("Firestore Tools")


@cli.command()
@click.argument('input', type=click.File('rb'), nargs=-1)
@click.argument('output', type=click.File('wb'))
def copy_file(input, output):
    """This script works similar to the Unix `cat` command but it writes
    into a specific file (which could be the standard output as denoted by
    the ``-`` sign).
    \b
    Copy stdin to stdout:
        inout - -
    \b
    Copy foo.txt and bar.txt to stdout:
        inout foo.txt bar.txt -
    \b
    Write stdin into the file foo.txt
        inout - foo.txt
    """
    for f in input:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            output.write(chunk)
            output.flush()


@cli.command()
def color():
    for color in all_colors:
        click.echo(click.style('I am colored %s' % color, fg=color))
    for color in all_colors:
        click.echo(click.style('I am colored %s and bold' % color,
                               fg=color, bold=True))
    for color in all_colors:
        click.echo(click.style('I am reverse colored %s' % color, fg=color,
                               reverse=True))

    click.echo(click.style('I am blinking', blink=True))
    click.echo(click.style('I am underlined', underline=True))


@cli.command()
def pager():
    """Demonstrates using the pager."""
    lines = []
    for x in range(200):
        lines.append('%s. Hello World!' % click.style(str(x), fg='green'))
    click.echo_via_pager('\n'.join(lines))


@cli.command()
@click.option('--count', default=8000, type=click.IntRange(1, 100000),
              help='The number of items to process.')
def progress(count):
    """Demonstrates the progress bar."""
    items = range(count)

    def process_slowly(item):
        time.sleep(0.002 * random.random())

    def filter(items):
        for item in items:
            if random.random() > 0.3:
                yield item

    with click.progressbar(items, label='Processing accounts',
                           fill_char=click.style('#', fg='green')) as bar:
        for item in bar:
            process_slowly(item)

    def show_item(item):
        if item is not None:
            return 'Item #%d' % item

    with click.progressbar(filter(items), label='Committing transaction',
                           fill_char=click.style('#', fg='yellow'),
                           item_show_func=show_item) as bar:
        for item in bar:
            process_slowly(item)

    with click.progressbar(length=count, label='Counting',
                           bar_template='%(label)s  %(bar)s | %(info)s',
                           fill_char=click.style(u'█', fg='cyan'),
                           empty_char=' ') as bar:
        for item in bar:
            process_slowly(item)

    with click.progressbar(length=count, width=0, show_percent=False,
                           show_eta=False,
                           fill_char=click.style('#', fg='magenta')) as bar:
        for item in bar:
            process_slowly(item)

    # 'Non-linear progress bar'
    steps = [math.exp( x * 1. / 20) - 1 for x in range(20)]
    count = int(sum(steps))
    with click.progressbar(length=count, show_percent=False,
                           label='Slowing progress bar',
                           fill_char=click.style(u'█', fg='green')) as bar:
        for item in steps:
            time.sleep(item)
            bar.update(item)


@cli.command()
def clear():
    """Clears the entire screen."""
    click.clear()


@cli.command()
def pause():
    """Waits for the user to press a button."""
    click.pause()


@cli.command()
def menu():
    """Shows a simple menu."""
    menu = 'main'
    while 1:
        if menu == 'main':
            click.echo('Main menu:')
            click.echo('  d: debug menu')
            click.echo('  q: quit')
            char = click.getchar()
            if char == 'd':
                menu = 'debug'
            elif char == 'q':
                menu = 'quit'
            else:
                click.echo('Invalid input')
        elif menu == 'debug':
            click.echo('Debug menu')
            click.echo('  b: back')
            char = click.getchar()
            if char == 'b':
                menu = 'main'
            else:
                click.echo('Invalid input')
        elif menu == 'quit':
            return


@cli.command()
@click.option('--cred', default='credential.json', help='Path to firetore credential (json) file')
@click.option('--output', default='.', help='Output folder, default: .')
@click.argument('path', metavar='{path-to-document-in-firestore}')
def read(cred, output, path):
    click.echo('Reading from firetore, credential file: %s' % (cred))
    cred = os.path.abspath(cred)
    output = os.path.abspath(output)
    click.echo('Document path: %s' % (path))
    click.echo('Output path: %s' % (output))
    fs = firestore.client(initialize_app(credentials.Certificate(cred)))
    # data = fs.collection('schools').get()
    # for item in data:
    #     print(json.dumps(item.to_dict()))
    #     break
    collections = fs.collections() # root collections
    # collections = fs.document('schools/dev').collections()  # root collections
    for col in collections:
        read_collection('', col)


def read_document(path, doc):
    print('Reading document:', path + '/' + doc.id)
    for col in doc.reference.collections():
        print(col.id)


def read_collection(path, colection):
    print('Reading collection:', path + '/' + colection.id)
    for doc in colection.get():
        print(doc.id)
        read_document(path + '/' + doc.id, doc)



@cli.command()
@click.option('--cred', default='credential.json', help='Firetore credential JSON file')
@click.option('--data', default='', help='Data to write to Firestore')
def write(cred, data):
    click.echo('Dropped the database')


if __name__ == '__main__':
    cli()
