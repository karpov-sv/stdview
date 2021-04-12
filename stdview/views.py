import os, glob, io

from flask import request, render_template, redirect, url_for, flash, send_file, send_from_directory
from flask import Response

import mimetypes
import magic

from astropy.time import Time
from astropy.io import fits

# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from skimage.transform import rescale
from stdpipe import cutouts, plots

from stdview.app import app, stdconf

@app.route('/')
def index():
    return redirect(url_for('view'))

def make_breadcrumb(path, base='ROOT', lastlink=False):
    breadcrumb = []

    while True:
        path1,leaf = os.path.split(path)

        if not lastlink and not breadcrumb:
            breadcrumb.append({'name':leaf, 'path':None})
        else:
            breadcrumb.append({'name':leaf, 'path':path})
        path = path1

        if not path:
            break

    breadcrumb.append({'name':base, 'path':'.'})
    breadcrumb.reverse()

    return breadcrumb

@app.route('/view/')
@app.route('/view/<path:path>')
def view(path=''):
    base = stdconf.get('basepath', '.')
    fullpath = os.path.join(base, path)

    contents = None
    files = None

    context = {'path': path, 'breadcrumb': make_breadcrumb(path)}

    if os.path.isdir(fullpath):
        # List of files in the directory

        files = []

        sort_key = 'name'

        for entry in os.scandir(fullpath):
            if entry.name[0] != '.' or stdconf.get('show_all'):
                stat = entry.stat()

                elem = {
                    'path': os.path.join(path, entry.name),
                    'name': entry.name,
                    'stat': stat,
                    'size': stat.st_size,
                    'time': Time(stat.st_mtime, format='unix'),
                    'mime': mimetypes.guess_type(entry.name)[0],
                    'is_dir': entry.is_dir(),
                }

                if elem['is_dir']:
                    elem['type'] = 'dir'
                elif elem['mime'] and 'image' in elem['mime']:
                    elem['type'] = 'image'
                elif elem['mime'] and 'text' in elem['mime']:
                    elem['type'] = 'text'
                elif elem['mime'] and 'fits' in elem['mime']:
                    elem['type'] = 'fits'
                elif os.path.splitext(entry.name)[1].lower().startswith('.fit'):
                    elem['type'] = 'fits'
                else:
                    elem['type'] = 'file'

                if elem['type'] == 'fits':
                    try:
                        hdus = fits.open(entry.path)
                        if hdus[0].data is None and hdus[1].name == 'IMAGE' and hdus[2].name == 'TEMPLATE':
                            elem['type'] = 'cutout'
                        elif hdus[0].data is not None:
                            elem['preview'] = True
                        hdus.close()
                    except:
                        pass

                files.append(elem)

        files = sorted(files, key=lambda _: _.get(sort_key))

        return render_template('files_list.html', files=files, **context)

    else:
        # Single file

        context['mime'] = magic.from_file(filename=fullpath, mime=True)
        context['magic_info'] = magic.from_file(filename=fullpath)
        context['stat'] = os.stat(fullpath)
        context['size'] = context['stat'].st_size
        context['time'] = Time(context['stat'].st_mtime, format='unix')

        context['mode'] = 'download'

        if 'text' in context['mime']:
            try:
                with open(fullpath, 'r') as f:
                    context['contents'] = f.read()
                context['mode'] = 'text'
            except:
                pass

        elif 'fits' in context['mime'] or os.path.splitext(path)[1].lower().startswith('.fit'):
            context['mode'] = 'fits'

            try:
                hdus = fits.open(fullpath) # FIXME: will it be closed?..
                context['fitsfile'] = hdus

                if hdus[0].data is None and hdus[1].name == 'IMAGE' and hdus[2].name == 'TEMPLATE':
                    context['mode'] = 'cutout'
                    context['cutout'] = cutouts.load_cutout(fullpath)
            except:
                pass

        elif 'image' in context['mime']:
            context['mode'] = 'image'

        return render_template('files_view.html', **context)

@app.route('/download/<path:path>/download', defaults={'attachment':True})
@app.route('/download/<path:path>', defaults={'attachment':False})
def download(path, attachment=True):
    base = stdconf.get('basepath', '.')
    fullpath = os.path.join(base, path)

    if os.path.isfile(fullpath):
        return send_file(os.path.abspath(fullpath), as_attachment=attachment)
    else:
        return "No such file"

@app.route('/preview/<path:path>', defaults={'ext':0})
@app.route('/preview/<path:path>/<int:ext>')
def preview(path, ext=0, width=None, minwidth=256, maxwidth=1024):
    """
    Preview FITS image as PNG
    """
    base = stdconf.get('basepath', '.')
    fullpath = os.path.join(base, path)

    # Optional parameters
    fmt = request.args.get('format', 'jpeg')
    quality = int(request.args.get('quality', 80))

    width = request.args.get('width', width)
    if width is not None:
        width = int(width)

    data = fits.getdata(fullpath, ext)

    figsize = [data.shape[1], data.shape[0]]

    if width is None:
        if figsize[0] < minwidth:
            width = minwidth
        elif figsize[0] > maxwidth:
            width = maxwidth

    if width is not None and figsize[0] != width:
        figsize[1] = width*figsize[1]/figsize[0]
        figsize[0] = width

    fig = Figure(facecolor='white', dpi=72, figsize=(figsize[0]/72, figsize[1]/72))
    ax = Axes(fig, [0., 0., 1., 1.])
    # ax.set_axis_off()
    fig.add_axes(ax)
    plots.imshow(data, ax=ax, show_axis=False, show_colorbar=False,
                 cmap=request.args.get('cmap', 'Blues_r'),
                 stretch=request.args.get('stretch', 'linear'),
                 qq=[float(request.args.get('qmin', 0.5)), float(request.args.get('qmax', 99.5))])

    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, quality=quality)

    return Response(buf.getvalue(), mimetype='image/%s' % fmt)

@app.route('/cutout/<path:path>')
def cutout(path, width=None):
    base = stdconf.get('basepath', '.')
    fullpath = os.path.join(base, path)

    cutout = cutouts.load_cutout(fullpath)

    figsize = [256*4, 256+40]

    fig = Figure(facecolor='white', dpi=72, figsize=(figsize[0]/72, figsize[1]/72), tight_layout=True)

    plots.plot_cutout(cutout, fig=fig, planes=['image', 'template', 'convolved', 'diff', 'mask'], cmap='Blues_r')

    buf = io.BytesIO()
    fig.savefig(buf, format="png")

    return Response(buf.getvalue(), mimetype='image/png')
