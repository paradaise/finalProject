#!/usr/bin/env python3
"""
Test Light Audio Preprocessing
=============================

Тестирование лёгкой предобработки (DC-removal + peak_normalize)
и сравнение с исходным сигналом.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from pathlib import Path
import json
from datetime import datetime
import logging

# Добавляем путь к модулям клиента
sys.path.append(str(Path(__file__).parent.parent / "raspberry_pi" / "client"))

from light_audio_preprocessor import LightAudioPreprocessor

# Suppress warnings
logging.getLogger().setLevel(logging.ERROR)


class LightPreprocessingTest:
    """Тестирование лёгкой предобработки"""

    def __init__(self):
        self.sample_rate = 16000
        self.preprocessor = LightAudioPreprocessor(target_peak=0.95)
        self.results = {}

    def generate_test_signals(self):
        """Генерирует тестовые сигналы"""
        duration = 3.0
        t = np.linspace(0, duration, int(self.sample_rate * duration))

        signals = {
            "speech_with_dc_offset": self.generate_speech_with_dc(t),
            "varying_amplitude": self.generate_varying_amplitude(t),
            "clipped_signal": self.generate_clipped_signal(t),
            "quiet_signal": self.generate_quiet_signal(t),
            "realistic_mixed": self.generate_realistic_mixed(t),
        }

        return signals

    def generate_speech_with_dc(self, t):
        """Речь с DC смещением"""
        # Базовая речь
        f0 = 250
        signal = np.sin(2 * np.pi * f0 * t)

        # Добавляем гармоники
        for harmonic in [2, 3, 4]:
            signal += 0.3 / harmonic * np.sin(2 * np.pi * f0 * harmonic * t)

        # Добавляем DC смещение (проблема, которую решаем)
        signal += 0.2  # DC offset

        # Огибающая
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
        signal *= envelope

        return signal

    def generate_varying_amplitude(self, t):
        """Сигнал с изменяющейся амплитудой"""
        f0 = 440  # A4 note
        signal = np.sin(2 * np.pi * f0 * t)

        # Изменяющаяся амплитуда (проблема нестабильности)
        amplitude = 0.3 + 0.7 * np.sin(2 * np.pi * 0.5 * t)
        signal *= amplitude

        return signal

    def generate_clipped_signal(self, t):
        """Заклиппированный сигнал"""
        f0 = 1000
        signal = 2.0 * np.sin(2 * np.pi * f0 * t)  # Амплитуда > 1.0

        # Добавляем шум
        signal += 0.1 * np.random.normal(0, 1, len(t))

        return signal

    def generate_quiet_signal(self, t):
        """Тихий сигнал"""
        f0 = 200
        signal = 0.1 * np.sin(2 * np.pi * f0 * t)  # Очень тихо

        # Добавляем гармоники
        for harmonic in [2, 3]:
            signal += 0.05 / harmonic * np.sin(2 * np.pi * f0 * harmonic * t)

        return signal

    def generate_realistic_mixed(self, t):
        """Реалистичный смешанный сигнал"""
        # Речь
        speech = 0.5 * np.sin(2 * np.pi * 250 * t)
        speech += 0.2 * np.sin(2 * np.pi * 500 * t)

        # Шум
        noise = 0.1 * np.random.normal(0, 1, len(t))

        # Импульсы
        impulse_times = [0.5, 1.5, 2.5]
        for impulse_time in impulse_times:
            idx = int(impulse_time * self.sample_rate)
            if idx < len(t):
                decay = np.exp(-np.arange(100) / 20)
                speech[idx : idx + 100] += 0.8 * decay

        # DC offset
        mixed = speech + noise + 0.15

        return mixed

    def analyze_signal(self, signal, name):
        """Анализирует сигнал до и после предобработки"""
        original = signal.copy()
        processed = self.preprocessor.preprocess(signal)

        analysis = {
            "original": {
                "mean": float(np.mean(original)),
                "std": float(np.std(original)),
                "rms": float(np.sqrt(np.mean(original**2))),
                "peak": float(np.max(np.abs(original))),
                "min": float(np.min(original)),
                "max": float(np.max(original)),
                "dynamic_range_db": 20
                * np.log10(
                    np.max(np.abs(original)) / (np.sqrt(np.mean(original**2)) + 1e-10)
                ),
            },
            "processed": {
                "mean": float(np.mean(processed)),
                "std": float(np.std(processed)),
                "rms": float(np.sqrt(np.mean(processed**2))),
                "peak": float(np.max(np.abs(processed))),
                "min": float(np.min(processed)),
                "max": float(np.max(processed)),
                "dynamic_range_db": 20
                * np.log10(
                    np.max(np.abs(processed)) / (np.sqrt(np.mean(processed**2)) + 1e-10)
                ),
            },
            "improvements": {
                "dc_removed": abs(float(np.mean(original)) - float(np.mean(processed))),
                "peak_normalized_to": float(np.max(np.abs(processed))),
                "amplitude_stabilized": (
                    float(np.std(processed)) / float(np.std(original))
                    if np.std(original) > 0
                    else 1.0
                ),
            },
        }

        return analysis

    def simulate_yamnet_compatibility(self, signal):
        """Симуляция совместимости с YAMNet"""
        # YAMNet предпочитает сигналы с пиковой амплитудой 0.8-1.0
        peak = np.max(np.abs(signal))
        mean_abs = np.mean(np.abs(signal))

        # Оценка качества
        if 0.8 <= peak <= 1.0:
            amplitude_score = 1.0
        elif 0.6 <= peak < 0.8:
            amplitude_score = 0.8
        elif 0.4 <= peak < 0.6:
            amplitude_score = 0.6
        else:
            amplitude_score = 0.4

        # Проверка на клиппинг
        clipping_ratio = np.sum(np.abs(signal) > 0.99) / len(signal)
        clipping_score = max(0, 1.0 - clipping_ratio * 10)

        # DC offset
        dc_offset = abs(np.mean(signal))
        dc_score = max(0, 1.0 - dc_offset * 5)

        overall_score = (amplitude_score + clipping_score + dc_score) / 3

        return {
            "overall_score": overall_score,
            "amplitude_score": amplitude_score,
            "clipping_score": clipping_score,
            "dc_score": dc_score,
            "peak_amplitude": float(peak),
            "mean_amplitude": float(mean_abs),
            "clipping_ratio": float(clipping_ratio),
            "dc_offset": float(dc_offset),
        }

    def create_comparison_plots(self, signals, save_dir):
        """Создаёт графики сравнения"""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)

        # 1. Time domain comparison
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("Light Preprocessing Comparison - Time Domain", fontsize=16)

        for i, (name, signal) in enumerate(signals.items()):
            ax = axes[i // 3, i % 3]

            original = signal
            processed = self.preprocessor.preprocess(signal)
            t = np.linspace(0, 3.0, len(signal))

            ax.plot(t, original, "b-", alpha=0.7, label="Original", linewidth=1)
            ax.plot(t, processed, "r-", alpha=0.9, label="Processed", linewidth=1.5)
            ax.set_title(name.replace("_", " ").title())
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim([-2, 2])

        plt.tight_layout()
        plt.savefig(
            save_dir / "time_domain_comparison.png", dpi=300, bbox_inches="tight"
        )
        plt.close()

        # 2. Amplitude statistics
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("Light Preprocessing - Amplitude Statistics", fontsize=16)

        signal_names = list(signals.keys())
        for i, name in enumerate(signal_names):
            ax = axes[i // 3, i % 3]

            original = signals[name]
            processed = self.preprocessor.preprocess(original)

            # Статистики
            orig_stats = [
                np.min(original),
                np.max(original),
                np.mean(original),
                np.std(original),
            ]
            proc_stats = [
                np.min(processed),
                np.max(processed),
                np.mean(processed),
                np.std(processed),
            ]
            labels = ["Min", "Max", "Mean", "Std"]

            x = np.arange(len(labels))
            width = 0.35

            ax.bar(
                x - width / 2,
                orig_stats,
                width,
                label="Original",
                alpha=0.7,
                color="blue",
            )
            ax.bar(
                x + width / 2,
                proc_stats,
                width,
                label="Processed",
                alpha=0.9,
                color="red",
            )

            ax.set_title(name.replace("_", " ").title())
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_dir / "amplitude_statistics.png", dpi=300, bbox_inches="tight")
        plt.close()

        # 3. YAMNet compatibility scores
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle("YAMNet Compatibility Scores", fontsize=16)

        for i, name in enumerate(signal_names):
            ax = axes[i // 3, i % 3]

            original = signals[name]
            processed = self.preprocessor.preprocess(original)

            orig_compat = self.simulate_yamnet_compatibility(original)
            proc_compat = self.simulate_yamnet_compatibility(processed)

            scores = ["Overall", "Amplitude", "Clipping", "DC Offset"]
            orig_values = [
                orig_compat["overall_score"],
                orig_compat["amplitude_score"],
                orig_compat["clipping_score"],
                orig_compat["dc_score"],
            ]
            proc_values = [
                proc_compat["overall_score"],
                proc_compat["amplitude_score"],
                proc_compat["clipping_score"],
                proc_compat["dc_score"],
            ]

            x = np.arange(len(scores))
            width = 0.35

            bars1 = ax.bar(
                x - width / 2,
                orig_values,
                width,
                label="Original",
                alpha=0.7,
                color="orange",
            )
            bars2 = ax.bar(
                x + width / 2,
                proc_values,
                width,
                label="Processed",
                alpha=0.9,
                color="green",
            )

            # Цветовая индикация
            for bar, value in zip(bars2, proc_values):
                if value >= 0.8:
                    bar.set_color("green")
                elif value >= 0.6:
                    bar.set_color("yellow")
                else:
                    bar.set_color("red")

            ax.set_title(name.replace("_", " ").title())
            ax.set_xticks(x)
            ax.set_xticklabels(scores)
            ax.set_ylim([0, 1.1])
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_dir / "yamnet_compatibility.png", dpi=300, bbox_inches="tight")
        plt.close()

    def run_test(self, save_dir):
        """Запускает полный тест"""
        print("🧪 Запуск теста лёгкой предобработки...")
        print("=" * 60)

        # Генерируем сигналы
        print("Генерация тестовых сигналов...")
        signals = self.generate_test_signals()

        # Анализируем каждый сигнал
        print("Анализ сигналов...")
        for name, signal in signals.items():
            print(f"  Анализ {name}...")
            self.results[name] = self.analyze_signal(signal, name)

        # Создаём визуализации
        print("Создание визуализаций...")
        self.create_comparison_plots(signals, save_dir)

        # Сохраняем результаты
        self.save_results(save_dir)

        print("Тест завершен!")
        return self.results

    def save_results(self, save_dir):
        """Сохраняет результаты теста"""
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)

        # Сохраняем JSON
        results_file = save_dir / "light_preprocessing_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"Результаты сохранены в {results_file}")


def main():
    """Основная функция"""
    # Создаём выходную директорию
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    # Запускаем тест
    tester = LightPreprocessingTest()
    results = tester.run_test(output_dir)

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТА ЛЁГКОЙ ПРЕДОБРАБОТКИ")
    print("=" * 60)

    # Выводим сводку
    for signal_name, data in results.items():
        print(f"\n{signal_name.upper().replace('_', ' ')}:")
        print(f"  Исходный пик: {data['original']['peak']:.3f}")
        print(f"  Обработанный пик: {data['processed']['peak']:.3f}")
        print(f"  DC offset удалён: {data['improvements']['dc_removed']:.3f}")
        print(
            f"  Стабилизация амплитуды: {data['improvements']['amplitude_stabilized']:.2f}x"
        )

        orig_compat = tester.simulate_yamnet_compatibility(
            np.sin(2 * np.pi * 440 * np.linspace(0, 3, 48000))
            * data["original"]["peak"]
        )
        proc_compat = tester.simulate_yamnet_compatibility(
            np.sin(2 * np.pi * 440 * np.linspace(0, 3, 48000))
            * data["processed"]["peak"]
        )

        print(
            f"  Совместимость YAMNet: {proc_compat['overall_score']:.2f} → {orig_compat['overall_score']:.2f}"
        )

    print(f"\nДетальные результаты и графики сохранены в: {output_dir}")
    print("Файлы созданы:")
    print("  - time_domain_comparison.png")
    print("  - amplitude_statistics.png")
    print("  - yamnet_compatibility.png")
    print("  - light_preprocessing_results.json")


if __name__ == "__main__":
    main()
