#coding: utf-8

import os
from collections import defaultdict
from datetime import datetime
import io
import math
from PIL import Image, ImageDraw, ImageFont
import statistics

histogram_dir = "histograms"

def get_player(players, player_id):
    player = None
    for player__ in players:
        if player__.id == player_id:
            player = player__
            break
    return player


def make_rate_histogram(players, ladder, bin_width=20):
    """ラダーごとのレートのヒストグラムを作る"""
    histogram = defaultdict(int)
    for player in players:
        latest_rate = player.latest_rate(ladder)
        bucket = bin_width * (latest_rate // bin_width)
        histogram[bucket] += 1
    return dict(sorted(histogram.items()))

def group_peaks(peaks, min_peak_distance=200):
    """山のグループ化"""
    if not peaks:
        return []
    groups = [[peaks[0]]]
    for p in peaks[1:]:
        if p - groups[-1][-1] < min_peak_distance:
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups

def pick_representative_peak(group):
    """グループにされた山々の代表値（平均）を返す"""
    return int(sum(group) / len(group))

def pick_peak_or_median(histogram, players, ladder, min_peak_distance=200):
    """山(peak)を探し、近くの山はグループにして、
    山が1つならそこを、山が複数なら中央値を返す。
    """
    keys = list(histogram.keys())
    values = list(histogram.values())
    peaks = []
    for i in range(1, len(values)-1):
        if values[i-1] < values[i] > values[i+1]:
            peaks.append(keys[i])

    grouped_peaks = group_peaks(peaks, min_peak_distance)
    if len(grouped_peaks) == 1:
        return pick_representative_peak(grouped_peaks[0]), "peak"
    else:
        if players:
            return int(statistics.median([player.latest_rate(ladder) for player in players])), "median"
        else:
            # 開発中はplayersがない時もあるのでとりあえず
            return 7000, "fixed"

def draw_histogram(histogram, highlight_rate, ladder, name, label, save=False):
    """自動で割り当てられる初期レートや、あるプレイヤーのレートがヒストグラムのどこにあるのか示す画像を返す"""
    width = 1500
    height = 600
    margin = 60
    spacing = 4

    bins = list(histogram.keys())
    values = list(histogram.values())
    max_count = max(values) if values else 1

    # 補間して曲線にする
    if len(bins) > 1:
        bin_min = min(bins)
        bin_max = max(bins)
        x_points = list(range(bin_min, bin_max + 1))
        y_points = [histogram.get(x, 0) for x in x_points]
        smooth_y = [
            (y_points[i-1] + y_points[i] + y_points[i+1]) / 3
            if 0 < i < len(y_points) - 1 else y_points[i] for i in range(len(y_points))
        ]
    else:
        x_points = bins
        smooth_y = values
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    big_font = ImageFont.truetype("fonts/NotoSansCJK-Regular.ttc", size=32)
    small_font = ImageFont.truetype("fonts/NotoSansCJK-Regular.ttc", size=14)
    scale_x = (width - 2 * margin) / (max(x_points) - min(x_points) + 1)
    scale_y = (height - 2 * margin) * 2.3 / max_count
    draw.text((width // 2 - 100, 10), f"{label} of {ladder}", fill="black", font=big_font)
    points = [
        (margin + (x - min(x_points)) * scale_x, height - margin - y * scale_y)
        for x, y in zip(x_points, smooth_y)
    ]
    for i in range(1, len(points)):
        draw.line([points[i-1], points[i]], fill="blue", width=2)
    highlight_x = margin + (highlight_rate - min(x_points)) * scale_x
    draw.line((highlight_x, margin, highlight_x, height - margin), fill="red", width=2)
    draw.text((highlight_x + 5, margin), f"{name} ( {highlight_rate} )", fill="black", font=big_font)

    # 横軸ラベル（レート、500刻み）
    label_start = (min(x_points) // 500) * 500
    label_end = (max(x_points) // 500 + 1) * 500
    for x in range(label_start, label_end + 1, 500):
        pos_x = margin + (x - min(x_points)) * scale_x
        draw.line((pos_x, height - margin, pos_x, height - margin + 5), fill="black")
        draw.text((pos_x - 10, height - margin + 8), str(x), fill="black", font=small_font)

    # 縦軸ラベル（数）
    for i in range(0, max_count + 1, max(1, math.ceil(max_count / 10))):
        pos_y = height - margin - i * scale_y
        draw.line((margin - 5, pos_y, margin, pos_y), fill="black")
        draw.text((5, pos_y - 8), str(i), fill="black", font=small_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    image_bytes = buf.read()
    if save:
        today = datetime.now().strftime("%Y-%m-%d")
        image_path = f"{histogram_dir}/{today}-{ladder}-histogram.png"
        with open(image_path, "wb") as f:
            f.write(image_bytes)

    return buf, image_bytes

def find_initial_rate(players, ladder, visualize=False, save=False):
    """指定したラダーのヒストグラムを作り、
    山が1つ（近くの山は1つの山としてグループ化される）ならその山を、
    山が2つ以上なら中央値を初期レートとして返す。
    methodは山を返したならpeak, 中央値を返したならmedian。
    visualizeしたなら画像も返す。
    """
    initial_rate = 7000 # playersが空の場合
    method = None
    image_bytes = None
    bytesio = None
    if players:
        histogram = make_rate_histogram(players, ladder)
        initial_rate, method = pick_peak_or_median(histogram, players, ladder)
        if visualize:
            bytesio, image_bytes = draw_histogram(histogram, initial_rate, ladder, name=method, label="Initial rate", save=save)
    print(f"find_initial_rate: initial_rate={initial_rate}, ladder={ladder}, method={method}")
    return initial_rate, method, image_bytes, bytesio

def visualize_player_rate(players, ladder, player_id):
    histogram = make_rate_histogram(players, ladder)
    player = get_player(players, player_id)
    if not player:
        return "player not found"
    rate = player.latest_rate(ladder)
    bytesio, image_bytes = draw_histogram(histogram, rate, ladder, name=player.name, label="Player rate", save=False)
    return bytesio, image_bytes

def draw_simple_rate_plot(rates, width=1500, height=600):
    margin = 60
    min_rate = min(rates)
    max_rate = max(rates)
    rate_range = max_rate - min_rate or 1

    num_points = len(rates)
    scale_x = (width - 2 * margin) / (num_points - 1)
    scale_y = (height - 2 * margin) / rate_range

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("fonts/NotoSansCJK-Regular.ttc", size=24)

    # 折れ線の点列
    points = [(
        margin + i * scale_x,
        height - margin - (rate - min_rate) * scale_y)
        for i, rate in enumerate(rates)]

    # 線を描く
    for i in range(1, len(points)):
        draw.line([points[i - 1], points[i]], fill="black", width=2)

    # 横軸（インデックス）にラベルを追加（5ステップごと）
    for i in range(num_points):
        if i % max(1, num_points // 20) == 0:
            x = margin + i * scale_x
            draw.line((x, height - margin, x, height - margin + 5), fill="black")
            if font:
                draw.text((x - 10, height - margin + 8), str(i), fill="black", font=font)

    # 縦軸（レート）にラベルを追加（5段階）
    for r in range(min_rate, max_rate + 1, max(1, rate_range // 5)):
        y = height - margin - (r - min_rate) * scale_y
        draw.line((margin - 5, y, margin, y), fill="black")
        if font:
            draw.text((5, y - 8), str(r), fill="black", font=font)

        # 水平な点線を引く（marginから右端まで）
        dash_length = 8
        gap_length = 6
        x = margin
        while x < width - margin:
            draw.line((x, y, min(x + dash_length, width - margin), y), fill="#333333")
            x += dash_length + gap_length

    # 結果画像をBytesIOで返す
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
