import cv2
import numpy as np
import threading

from utils import *


def main(video_path, contours, is_visualized=False, video_save_path=None):
    cap = cv2.VideoCapture(video_path)
    frame_per_second = cap.get(cv2.CAP_PROP_FPS)

    if video_save_path:
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        out_shape = int(cap.get(3)), int(cap.get(4)) # width, height
        out = cv2.VideoWriter(video_save_path, fourcc, frame_per_second, out_shape, True)
    
    frame_cur = 0
    frame_step = frame_per_second
    while cap.isOpened():
        is_next, frame = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_cur)
        frame_cur += frame_step
        if not is_next:
            break

        pool = []
        for contour_index in contours.keys():
            pool.append(
                threading.Thread(
                    target = check, 
                    args = (frame, contours, contour_index)
                )
            )
        for t in pool:
            t.start()
        for t in pool:
            t.join()

        if is_visualized or video_save_path:
            for contour_index, val in contours.items():
                contour = val['contour']
                flags = val['result']['flags']
                flags_cell = val['result']['flags_cell']
                # print(flags_cell)
                values = val['result']['values']
                values_cell = val['result']['values_cell']
                color = (0, 0, 255) if any(flags.values()) else (0, 255, 0)
                test_pos_x = contour[:, 0].min()
                test_pos_y = contour[:, 1].max()
                text = f'{contour_index} | ' + ' | '.join([f'{k}: {v}' for k, v in flags.items()])
                cv2.putText(
                    frame, text, (test_pos_x, test_pos_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, color, 2
                )
                text = ' | '.join([f'{k}: {round(v, 4)}' for k, v in values.items()])
                cv2.putText(
                    frame, text, (test_pos_x, test_pos_y + 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, color, 2
                )
                for mean_val, std_val, median_val, coords, flag_1 in zip(values_cell['all_mean'], values_cell['all_std'],
                                                         values_cell['all_median'], values_cell['all_coords'], flags_cell['is_warning_cell']):
                    coords = [list(coords)]
                    coords += np.tile(coords[0], (4, 1))
                    coords = coords // 2
                    coords += np.tile(contour[[0]], (4, 1)) + np.array([[50, 200], [50, 200], [50, 200], [50, 200]])
                    coords[1] += [20, 0]
                    coords[2] += [20, 20]
                    coords[3] += [0, 20]
                    # print(mean_val, std_val, median_val)


                    color_cell = (0, 0, 255) if flag_1 else (0, 255, 0)
                    cv2.fillPoly(frame, [coords], color=color_cell)


                    cv2.drawContours(frame, [coords], 0, (255, 255, 255), 2)
                cv2.drawContours(frame, [contour], 0, color, 2)
            if is_visualized:
                cv2.imshow('Frame', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            if video_save_path:
                out.write(frame)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    contours = [
        {
            'contour': np.array([[1155, 660], [1412, 625], [1412, 677], [1162, 715]]),
            'bounds': {
                'mean': (200, 230),
                'median': (200, 230),
                'std': (0, 100),
            },
            'warnings': {
                'mean': 0.5,
                'median': 0.5,
                'std': 1.0,
            },
        },
        {
            'contour': np.array([[685, 645], [980, 610], [980, 680], [710, 710]]),
            'bounds': {
                'mean': (200, 230),
                'median': (200, 230),
                'std': (0, 100),
            },
            'warnings': {
                'mean': 0.5,
                'median': 0.5,
                'std': 1.0,
            },
        },
        {
            'contour': np.array([[262, 405], [492, 365], [497, 400], [267, 435]]),
            'bounds': {
                'mean': (140, 190),
                'median': (140, 190),
                'std': (0, 100),
            },
            'warnings': {
                'mean': 0.5,
                'median': 0.5,
                'std': 1.0,
            },
        },
    ]
    contours = {i: v for i, v in enumerate(contours)}
    main(
        video_path = '2023-07-12_03_49_11_03_55_00_4306a3db50ad28fc.mp4',
        contours = contours,
        is_visualized = True,
        video_save_path = 'out_2023-07-12_03_49_11_03_55_00_4306a3db50ad28fc.mp4',
    )

    # TODO:
    # 1) Подправить пороговые значения main() / подобрать оптимальные значения каллибровки в utils
    # 2) измнение флага is_outlier
    # 3) тест по двум параметрам яркости и красочности в формате HUE

