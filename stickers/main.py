import codecs
import gzip
import io
import json
import os
import random

import fontTools
import lottie
from lottie.nvector import NVector
from lottie.objects.shapes import Group, Path
from lottie.utils import animation
from lottie.utils.font import BezierPen

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "impact.ttf")


def closest(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]


def validate_and_fix(an):
    # check and fix framerate
    if an.frame_rate not in (30, 60):
        print("fixing frame rate")
        an.frame_rate = closest([30, 60], an.frame_rate)

    # check and fix frames count (no more than 180, 3 seconds)
    if (an.out_point - an.in_point) / an.frame_rate > 3:
        print("fixing duration")
        an.out_point = 180

    if an.width != 512 or an.height != 512:
        print("fixing width and height")
        an.width = 512
        an.height = 512

    if an.threedimensional and an.threedimensional != 0:
        print("fixing 3d layers")
        an.threedimensional = 0


def tg_compress(d):
    my_list = d.items() if isinstance(d, dict) else enumerate(d)

    for k, v in my_list:
        if isinstance(v, dict) or isinstance(v, list):
            # remove zero arrays

            if all([q == [0, 0] for q in d]):
                d = []
            # elif v == [0, 0]:
            #     d[k] = []
            else:
                tg_compress(v)
        else:
            if isinstance(v, float):
                # decrease float precision
                d[k] = round(v, 2)


class FontRenderer:
    def __init__(self, filename):
        self.filename = filename
        self.font = fontTools.ttLib.TTFont(filename)
        self.glyphset = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap() or {}

    def glyph_beziers(self, name, offset=NVector(0, 0)):
        pen = BezierPen(self.glyphset, offset)
        self.glyphset[name].draw(pen)
        return pen.beziers

    def glyph_shapes(self, name, offset=NVector(0, 0)):
        beziers = self.glyph_beziers(name, offset)
        return [Path(bez) for bez in beziers]

    def glyph_group(self, name):
        group = Group()
        group.name = name
        group.shapes = self.glyph_shapes(name) + group.shapes
        return group

    def render(self, text, size, pos=None, on_missing=None):
        """!
        Renders some text

        @param text         String to render
        @param size         Font size (in pizels)
        @param[in,out] pos  Text position
        @param on_missing   Callable on missing glyphs, called with:
        - Character as string
        - Font size
        - [in, out] Character position
        - Group shape

        @returns a Group shape, augmented with some extra attributes:
        - line_height   Line height

        """
        scale = size / self.font.tables["head"].unitsPerEm
        line_height = self.font.tables["head"].yMax * scale
        group = Group()
        group.name = text
        if pos is None:
            pos = NVector(0, 0)
        # group.transform.scale.value = NVector(100, 100) * scale
        for ch in text:
            if ch == "\n":
                pos.x = 0
                pos.y += line_height
                continue

            chname = self.cmap.get(ord(ch)) or self.font._makeGlyphName(ord(ch))
            if chname in self.glyphset:
                glyph_shapes = self.glyph_shapes(chname, pos / scale)
                glyph_shape_group = group.add_shape(Group()) if len(glyph_shapes) > 1 else group

                for sh in glyph_shapes:
                    sh.shape.value.scale(scale)
                    glyph_shape_group.add_shape(sh)

                pos.x += self.glyphset[chname].width * scale
            elif on_missing:
                on_missing(ch, size, pos, group)

        group.line_height = line_height
        return group

    def __repr__(self):
        return "<FontRenderer %r>" % self.filename


class TextPrinter(object):
    def __init__(self, file, selected_animation=None):
        self.infile_path = file
        self.tg_sticker = self._load_sticker_file(file)

        self.default_animations = ("shake", "spring_pull_top", "spring_pull_right")
        self.selected_animation = selected_animation or random.choice(self.default_animations)

    def _load_sticker_file(self, file):
        lottie_json = lottie.parsers.tgs.parse_tgs_json(file)

        return lottie.objects.animation.Animation.load(lottie_json)

    def add_text(self, top_line: str = "", middle_line: str = "", bottom_line: str = ""):
        layer = lottie.objects.ShapeLayer()
        self.tg_sticker.insert_layer(0, layer)

        if top_line is not None and len(top_line):
            layer.add_shape(self.create_text_line(top_line))
        if bottom_line is not None and len(bottom_line):
            layer.add_shape(self.create_text_line(bottom_line, bottom=True))
        if middle_line is not None and len(middle_line):
            layer.add_shape(self.create_text_line(middle_line, middle=True))

        validate_and_fix(self.tg_sticker)

        output_dict = self.tg_sticker.to_dict()

        tg_compress(output_dict)

        output = io.BytesIO()
        with gzip.open(output, "w") as g:
            json.dump(output_dict, codecs.getwriter("utf-8")(g), separators=(",", ":"), ensure_ascii=False)
        output.seek(0)
        return output

    def create_text_line(self, text: str, middle: bool = False, bottom: bool = False):
        line_group = lottie.objects.Group()

        line_shapes_group = FontRenderer(FONT_PATH).render(text, size=64, pos=lottie.nvector.NVector(0, 0))
        text_length = len(text)
        tg_seconds = self.tg_sticker.out_point / self.tg_sticker.frame_rate
        self.selected_animation = self.selected_animation if tg_seconds >= 1.5 else "shake"

        for index, letter_shape in enumerate(line_shapes_group.shapes):
            letter_group = line_group.add_shape(lottie.objects.Group())
            letter_group.add_shape(letter_shape)
            # make letters moving
            if self.selected_animation == "shake":
                animation.shake(
                    letter_group.transform.position, 5, 5, 0, self.tg_sticker.out_point, self.tg_sticker.frame_rate // 2
                )
            elif self.selected_animation == "spring_pull_top":
                letter_group.transform.position.value = lottie.Point(0, -512)
                end_time = self.tg_sticker.out_point // 1.7
                start_time = index * (end_time / text_length)
                if start_time < end_time:
                    animation.spring_pull(
                        letter_group.transform.position, lottie.Point(0, 0), start_time, end_time, 7, 7
                    )
            # elif self.selected_animation == 'spring_pull_right':
            #     letter_group.transform.position.value = Point(512 * 2, 0)
            #     total_frames_for_effect = self.tg_sticker.out_point // 1.7
            #     animation.spring_pull(letter_group.transform.position, Point(0, 0),
            #                           index * (total_frames_for_effect / text_length),
            #                           self.tg_sticker.out_point // 1.7, 7, 7)

        line_group_x = (512 - line_shapes_group.bounding_box().width) / 2
        line_group_y = 80
        if bottom:
            line_group_y = 512 - 50
        elif middle:
            line_group_y = 512 / 2 - 30

        line_group.transform.position.value.x = line_group_x
        line_group.transform.position.value.y = line_group_y

        if self.selected_animation == "spring_pull_right":
            line_group.transform.position.value.x = 512
            if bottom:
                line_group.transform.position.value.x = -512
            if middle:
                line_group.transform.position.value.x = 0
            animation.spring_pull(
                line_group.transform.position,
                lottie.Point(line_group_x, line_group_y),
                0,
                self.tg_sticker.out_point // 2,
                7,
                7,
            )

        line_group.add_shape(lottie.objects.Fill(lottie.Color(1, 1, 1)))
        line_group.add_shape(lottie.objects.Stroke(lottie.Color(0, 0, 0), 7))

        return line_group
