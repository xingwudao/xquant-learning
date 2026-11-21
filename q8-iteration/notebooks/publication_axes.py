"""Publication-only axis formatting; never changes plotted observations."""
import re
from matplotlib.ticker import Formatter

# These chart series are already in percentage units, or have an explicit
# ratio-to-percentage formatter in the Notebook. Never multiply here again.
PERCENT_AXES = {
    '收益率', '最终收益率', '累计收益率', '年化波动率', '年收益率',
    '月收益率', '目标权重', '止损阈值', '回撤', '现金残余占比',
    '价格差异率', '市场年化波动率', '净值相对差异的 63 日滚动均值',
}
BOOK_ONLY_TITLES = {'03-iter1-rebal-freq.png', '04-iter2-vol-filter.png'}


class PercentSuffix(Formatter):
    """Keep the existing percent scale (including any earlier x100 formatter)."""
    def __init__(self, original):
        self.original = original

    def set_axis(self, axis):
        super().set_axis(axis)
        self.original.set_axis(axis)

    def set_locs(self, locs):
        super().set_locs(locs)
        self.original.set_locs(locs)

    def __call__(self, value, pos=None):
        text = self.original(value, pos).replace('-', '−')
        if not text:
            return text
        if value == 0:
            return '0%'
        return text if text.endswith('%') else text + '%'


def apply_publication_axes(fig):
    """Percent ticks and consistent spacing at a nominal 15 cm print width.

    Apply after the plotting/layout commands, before saving or displaying.
    Percentage-point, NAV, IC and Sharpe axes are deliberately not converted.
    """
    fig.canvas.draw()
    scale = fig.get_figwidth() / (150 / 25.4)
    active = [ax for ax in fig.axes if ax.axison]
    for ax in active:
        ax.tick_params(axis='both', which='major', pad=2.0 * scale)
        ax.xaxis.labelpad = ax.yaxis.labelpad = 3.0 * scale
        for axis, get_label, set_label in (
            (ax.xaxis, ax.get_xlabel, ax.set_xlabel),
            (ax.yaxis, ax.get_ylabel, ax.set_ylabel),
        ):
            name = get_label()
            if name in PERCENT_AXES or re.search(r'/%$|[（(]\s*%\s*[）)]$', name):
                set_label(re.sub(r'/%$|[（(]\s*%\s*[）)]$', '', name).rstrip())
                old = axis.get_major_formatter()
                if not isinstance(old, PercentSuffix):
                    axis.set_major_formatter(PercentSuffix(old))

    # A colorbar is part of its plot, not an independent side-by-side panel.
    panels = [ax for ax in active if ax.get_label() != '<colorbar>']
    horizontal = any(
        a.get_position().x1 <= b.get_position().x0 + 0.002
        and min(a.get_position().y1, b.get_position().y1)
        > max(a.get_position().y0, b.get_position().y0) + 0.02
        for a in panels for b in panels if a is not b
    )
    engine = fig.get_layout_engine()
    if engine is not None and type(engine).__name__ == 'ConstrainedLayoutEngine':
        # Inches at source size; scaled to a common clearance in print.
        engine.set(w_pad=6.0 * scale / 72, h_pad=4.0 * scale / 72)
        if horizontal:
            engine.set(wspace=0.12)
    elif horizontal:
        fig.subplots_adjust(wspace=max(fig.subplotpars.wspace, 0.48))

    # Keep right-panel y labels perceptually separate from the left panel.
    for _ in range(8):
        fig.canvas.draw()
        if not horizontal:
            break
        renderer = fig.canvas.get_renderer()
        target = 10.0 * scale * fig.dpi / 72
        too_close = False
        for right in panels:
            rb = right.get_position()
            lefts = [a for a in panels if a is not right
                     and a.get_position().x1 <= rb.x0 + 0.002
                     and min(a.get_position().y1, rb.y1)
                     > max(a.get_position().y0, rb.y0) + 0.02]
            if not lefts:
                continue
            left = max(lefts, key=lambda a: a.get_position().x1)
            labels = [t for t in right.get_yticklabels() if t.get_visible() and t.get_text()]
            if right.get_ylabel():
                labels.append(right.yaxis.label)
            x0 = min((t.get_window_extent(renderer).x0 for t in labels),
                     default=right.bbox.x0)
            clearance = target
            if right.get_ylabel():
                label_box = right.yaxis.label.get_window_extent(renderer)
                own_distance = max(0, right.bbox.x0 - label_box.x1)
                # The label should look attached to its own plot, not centered
                # in the gutter or closer to the preceding plot.
                clearance = max(clearance, 1.5 * own_distance)
            if x0 - left.bbox.x1 < clearance:
                too_close = True
        if not too_close:
            break
        if engine is not None and type(engine).__name__ == 'ConstrainedLayoutEngine':
            settings = engine.get()
            engine.set(wspace=settings['wspace'] + 0.04)
        else:
            fig.subplots_adjust(wspace=fig.subplotpars.wspace + 0.06)
    fig.canvas.draw()


def configure_publication_axes():
    """Install the display hook once; useful for independently run Notebooks."""
    from matplotlib.figure import Figure
    from pathlib import Path
    import matplotlib.pyplot as plt
    if getattr(Figure.savefig, '_publication_axes', False):
        return
    previous = Figure.savefig

    def savefig(fig, *args, **kwargs):
        apply_publication_axes(fig)
        path = args[0] if args else kwargs.get('fname')
        hide_title = isinstance(path, (str, Path)) and Path(path).name in BOOK_ONLY_TITLES
        titles = [ax.get_title() for ax in fig.axes]
        if hide_title:
            for ax in fig.axes:
                ax.set_title('')
        try:
            return previous(fig, *args, **kwargs)
        finally:
            if hide_title:
                for ax, title in zip(fig.axes, titles):
                    ax.set_title(title)

    savefig._publication_axes = True
    Figure.savefig = savefig
    previous_show = plt.show

    def show(*args, **kwargs):
        for number in plt.get_fignums():
            apply_publication_axes(plt.figure(number))
        return previous_show(*args, **kwargs)

    plt.show = show
