# ===============================================================================
# Copyright 2017 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os

import time
from chaco.array_plot_data import ArrayPlotData
from chaco.axis import PlotAxis
from chaco.plot import Plot
from chaco.plot_containers import VPlotContainer
from chaco.plot_graphics_context import PlotGraphicsContext
from enable.component import Component
from enable.component_editor import ComponentEditor
from numpy import array, diff, hstack, asarray, r_, ones, convolve, linspace
from pyface.timer.timer import Timer
from scipy import interpolate
from traits.api import HasTraits, Instance, Enum, Button
from traitsui.api import View, UItem, Item


BGCOLOR = 'green'
WIDTH = 900
HEIGHT = WIDTH * 9 / 16.

FPS = 10.
ALTITUDE = 5
GROUNDSPEED = 6

class Maker(HasTraits):
    plot = Instance(Component)
    container = Instance(VPlotContainer)
    plot_data = Instance(ArrayPlotData)
    interpolation_kind = Enum('linear', 'nearest', 'zero', 'slinear', 'quadratic', 'cubic')
    test = Button

    def __init__(self, *args, **kw):
        super(Maker, self).__init__(*args, **kw)

    def _test_fired(self):
        p = '/Users/ross/UAV/logs/GPS 1_2017-09-08_18-35-55.csv'
        # p = '/Users/ross/UAV/logs/GPS 1_2017-09-09_18-44-19.csv'
        self.interpolation_kind = 'cubic'
        self.make_animation(p)

    def make_animation(self, input_path):
        output_root = '/Users/ross/UAV/log_animations/'
        cnt = 0
        while 1:
            outdir = os.path.join(output_root, '{}{}'.format(os.path.basename(input_path), cnt))
            if not os.path.isdir(outdir):
                os.mkdir(outdir)
                break
            cnt += 1

        pd = self.plot_data
        pd.set_data('x', [])
        pd.set_data('alt', [])
        pd.set_data('gs', [])

        p = self.plot
        p.x_grid.visible = False
        p.x_axis.axis_line_weight = 4
        p.y_axis.axis_line_weight = 4
        p.x_axis.axis_label_font = 'modern 18'
        p.y_axis.axis_label_font = 'modern 18'
        p.y_axis.title = 'Altitude (m)  Ground Speed (m/s)'
        p.x_axis.title = 'Time (s)'

        p.plot(('x', 'alt'), color='orange', line_width=6, bgcolor=BGCOLOR)
        p.plot(('x', 'gs'), color='blue', line_width=6, bgcolor=BGCOLOR)

        xs, alt, gs = self._load_gps_file(input_path)
        YOFFSET = alt.min()
        max_x = 60
        max_num_points = max_x*FPS
        p.index_range.high = max_x + 5
        p.value_range.low = -0.5
        # p.value_range.high = (alt.max()-YOFFSET) * 1.1

        def gen():
            for xi, ai, gi in zip(xs, alt, gs):
                # print ai, gi, ai-YOFFSET

                yield xi, ai-YOFFSET, gi

        gg = gen()

        gc = PlotGraphicsContext((WIDTH, HEIGHT), dpi=150)

        def save_frame(imp=None):
            if imp is None:
                imp = 'image{:05n}.png'.format(self.cnt)

            self.container.do_layout(force=True)
            gc.render_component(self.container)
            gc.save(os.path.join(outdir, imp))

        # self.cnt = 0
        def update():
            xs = pd.get_data('x')
            alts = pd.get_data('alt')
            gs = pd.get_data('gs')

            x, a, g = next(gg)
            nx = hstack((xs[-max_num_points + 1:], [x]))
            nalts = hstack((alts[-max_num_points + 1:], [a]))
            ngs = hstack((gs[-max_num_points + 1:], [g]))

            pd.set_data('x', nx)
            pd.set_data('alt', nalts)
            pd.set_data('gs', ngs)
            if x > max_x:
                p.index_range.high = x + 5
            # p.invalidate_and_redraw()
            # save_frame()
            # self.cnt+=1
        if 1:
            cnt = 0
            while 1:
                try:
                    update()
                except StopIteration:
                    break

                save_frame('image{:05n}.jpg'.format(cnt))
                cnt += 1
            print 'output finished', cnt

        else:
            self.timer = Timer(1/FPS*1000, update)

    def _load_gps_file(self, p):
        xs, alt, gs = [], [], []
        with open(p, 'r') as rfile:
            _header = rfile.readline()

            for line in rfile:
                row = line.strip().split(',')
                xs.append(float(row[2]))
                alt.append(float(row[ALTITUDE]))
                gs.append(float(row[GROUNDSPEED]))

        xs, alt, gs = array(xs)*3, array(alt), array(gs)
        falt = interpolate.interp1d(xs, alt, kind=self.interpolation_kind)
        fgs = interpolate.interp1d(xs, gs, kind=self.interpolation_kind)

        total_time = xs[-1]-xs[0]

        n = total_time * FPS
        print 'total frames {}. total_time={}, fps={}'.format(n, total_time, FPS)
        xs = linspace(xs[0], xs[-1], n)

        return xs, falt(xs), fgs(xs)

    def _container_factory(self):
        container = VPlotContainer(bgcolor=BGCOLOR, use_backbuffer=False)
        # container.bgcolor = BGCOLOR
        container.outer_bounds = (WIDTH, HEIGHT)
        container.add(self.plot)
        return container

    def _plot_factory(self):
        plot = Plot(self.plot_data,
                    padding_top=300,
                    fill_padding=True)
        plot.bgcolor = BGCOLOR
        return plot

    def traits_view(self):

        v = View(UItem('test'),
                 UItem('plot', editor=ComponentEditor(width=WIDTH, height=HEIGHT)), )
        return v

    def _container_default(self):
        return self._container_factory()

    def _plot_default(self):
        return self._plot_factory()

    def _plot_data_default(self):
        return ArrayPlotData()


def main():
    m = Maker()
    m.configure_traits()


if __name__ == '__main__':
    main()
# ============= EOF =============================================
