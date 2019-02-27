import json
import math
import os
import random
import re
import time
from datetime import timedelta

import click
from firebase_admin import firestore, initialize_app, credentials

all_colors = 'black', 'red', 'green', 'yellow', 'blue', 'magenta', \
             'cyan', 'white', 'bright_black', 'bright_red', \
             'bright_green', 'bright_yellow', 'bright_blue', \
             'bright_magenta', 'bright_cyan', 'bright_white'


@click.group()
def cli():
    """Firetore CLI tools by Thuc Nguyen (https://github.com/thucnc)

     Example:
         $ firestoretools read -c credentials.json -o data -t collection -l -1 -e schools/dev /
    """
    click.echo("Firestore Tools by Thuc Nguyen (https://github.com/ncthuc)")


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
    """
    Test color output
    :return:
    """
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
    steps = [math.exp(x * 1. / 20) - 1 for x in range(20)]
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


total_doc_count = 0
start_time = 0


def need_exclude(path, exclude_pattern):
    path = path.replace('_collections/', '/')
    return re.match(exclude_pattern, path) is not None


@cli.command()
@click.option('-c', '--cred', default='credential.json',
              type=click.Path(exists=True, readable=True, dir_okay=False),
              prompt='JSON credential file',
              help='Path to Firestore credential (json) file')
@click.option('-o', '--output', default='data',
              type=click.Path(exists=True, readable=True, file_okay=False, writable=True),
              prompt='Output folder', help='Output folder')
@click.option('-l', '--depth', default=1, help='Recursion maximum depth level , -1 for infinite recursion')
@click.option('-t', '--type', type=click.Choice(['document', 'collection']), default='document',
              help='Start reading with a document or a collection')
@click.option('-e', '--exclude', default='', help='Exclude path pattern (regex)')
@click.argument('path', metavar='{path to document/collection in firestore}')
def read(cred, output, depth, type, exclude, path):
    """
    Read data (document / collection) from Firestore recursively and save to local file system

    \b
    :param cred:
    :param output:
    :param depth:
    :param type:
    :param exclude:
    :param path:
    :return:
    """
    click.echo('Reading from firetore, credential file: %s' % (cred))
    cred = os.path.abspath(cred)
    output = os.path.abspath(output)
    click.echo('Document path: %s' % path)
    click.echo('Output path: %s' % output)

    if depth<0:
        depth = 1000000

    if path and path.startswith('/'):
        path = path[1:]

    if os.listdir(output):
        click.echo('\nError: folder "%s" is not empty' % output)
        return

    global total_doc_count
    global start_time
    total_doc_count = 0
    start_time = time.time()
    fs = firestore.client(initialize_app(credentials.Certificate(cred)))
    # data = fs.collection('schools').get()
    # for item in data:
    #     print(json.dumps(item.to_dict()))
    #     break
    if not path or path == '/': # get all root collections
        collections = fs.collections()  # root collections
        # collections = fs.document('schools/dev').collections()  # root collections
        for col in collections:
            read_collection(output, col.id, col, 1, depth, exclude)
    elif type=='document':
        doc = fs.document(path).get()
        read_document(output, path, doc, 1, depth, exclude)
    else: # 'collection'
        col = fs.collection(path)
        read_collection(output, path, col, 1, depth, exclude)


def read_document(output, path, doc, l, max_depth, exclude):
    if need_exclude(path, exclude):
        click.echo(click.style("Excluded document '%s'." % path, fg='red', bold=True))
        return
    global total_doc_count
    if l > max_depth:
        return
    print('### Reading document (depth=%s):' % l, path)
    # print("doc #%s:" % doc.id, len(doc.to_dict()))
    f = os.path.join(output, path.replace('/', os.path.sep))
    with open(f, 'w') as of:
        # print('file:', f)
        json.dump(doc.to_dict(), of)

    total_doc_count += 1
    global start_time
    if total_doc_count % 10 == 0:
        click.echo(click.style("Total documents saved: %d..." % total_doc_count, fg='green', bold=True))
        click.echo(click.style("Elapsed time: %s..." % str(timedelta(seconds=(time.time()-start_time))), fg='yellow', bold=True))

    for col in doc.reference.collections():
        read_collection(output, path + '_collections/' + col.id, col, l+1, max_depth, exclude)


def read_collection(output, path, colection, l, max_depth, exclude):
    if need_exclude(path, exclude):
        click.echo(click.style("Excluded collection '%s'." % path, fg='red', bold=True))
        return
    if l > max_depth:
        return
    print('### Reading collection: (depth=%s)' % l, path)
    folder = os.path.join(output, path.replace('/', os.path.sep))
    if not os.path.exists(folder):
        os.makedirs(folder)

    for doc in colection.get():
        read_document(output, path + '/' + doc.id, doc, l+1, max_depth, exclude)


@cli.command()
@click.option('--cred', default='credential.json', help='Firetore credential JSON file')
@click.option('--data', default='', help='Data to write to Firestore')
def write(cred, data):
    click.echo('Dropped the database')


if __name__ == '__main__':
    # cli()
    print(need_exclude('schools/dev_collections/', '$schools/d.*v'))
