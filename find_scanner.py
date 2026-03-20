import os
import sys
import time
from pathlib import Path
from typing import List, Generator
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
import platform

# Для цветного вывода в Windows 11
if platform.system() == "Windows":
    ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)

class Colors:
    """Класс для цветного вывода"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class ProgressBar:
    """Класс для отображения прогресс-бара"""
    
    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0
        self.lock = threading.Lock()
        
    def update(self, increment: int = 1):
        """Обновление прогресс-бара"""
        with self.lock:
            self.current += increment
            if self.current > self.total:
                self.current = self.total
            self._display()
    
    def _display(self):
        """Отображение прогресс-бара"""
        percent = (self.current * 100) // self.total if self.total > 0 else 0
        filled = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        sys.stdout.write(f'\r{Colors.CYAN}[{bar}]{Colors.RESET} {percent}% ({self.current}/{self.total})')
        sys.stdout.flush()
        
        if self.current == self.total:
            print() 

class FileScanner:
    """Класс для сканирования файловой системы"""
    
    def __init__(self, extension: str, max_workers: int = 8):
        self.extension = extension.lower()
        self.max_workers = max_workers
        self.found_files = []
        self.total_dirs = 0
        self.processed_dirs = 0
        
    def get_all_drives(self) -> List[str]:
        """Получение всех доступных дисков в Windows"""
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    
    def get_directories(self, root_path: str) -> List[str]:
        """Рекурсивный сбор всех директорий"""
        directories = []
        try:
            for root, dirs, files in os.walk(root_path):
                directories.append(root)
                dirs[:] = [d for d in dirs if not d.startswith('$')]
        except (PermissionError, OSError):
            pass
        return directories
    
    def scan_directory(self, directory: str) -> List[str]:
        """Сканирование одной директории на наличие файлов с нужным расширением"""
        found = []
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and item.lower().endswith(f'.{self.extension}'):
                    found.append(item_path)
        except (PermissionError, OSError):
            pass
        return found
    
    def scan_system(self, progress_callback=None) -> List[str]:
        """Сканирование всей системы"""
        drives = self.get_all_drives()
        print(f"{Colors.GREEN}Найдено дисков: {', '.join(drives)}{Colors.RESET}\n")
        
        all_files = []
        
        for drive in drives:
            print(f"{Colors.BOLD}{Colors.BLUE}Сканирование диска {drive}{Colors.RESET}")
            
            # Сбор всех директорий на диске
            print(f"{Colors.YELLOW}Сбор директорий...{Colors.RESET}")
            directories = self.get_directories(drive)
            self.total_dirs = len(directories)
            
            if self.total_dirs == 0:
                print(f"{Colors.RED}Нет доступных директорий для сканирования{Colors.RESET}\n")
                continue
            
            print(f"{Colors.GREEN}Найдено директорий: {self.total_dirs}{Colors.RESET}")
            
            # Создаем прогресс-бар
            progress = ProgressBar(self.total_dirs)
            self.processed_dirs = 0
            
            # Многопоточное сканирование
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.scan_directory, directory): directory 
                          for directory in directories}
                
                for future in as_completed(futures):
                    try:
                        files = future.result()
                        all_files.extend(files)
                        self.processed_dirs += 1
                        progress.update()
                        
                        # Выводим найденные файлы
                        for file in files:
                            print(f"\n{Colors.GREEN}Найден: {file}{Colors.RESET}")
                            
                    except Exception as e:
                        pass
            
            print(f"\n{Colors.CYAN}Сканирование диска {drive} завершено{Colors.RESET}\n")
        
        return all_files

def main():
    """Основная функция"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}     СКАНЕР ФАЙЛОВ WINDOWS 11 - ПОИСК ПО РАСШИРЕНИЮ{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}\n")
    
    while True:
        extension = input(f"{Colors.YELLOW}Введите расширение файла (например: pdf, txt, exe): {Colors.RESET}").strip()
        if extension:
            break
        print(f"{Colors.RED}Расширение не может быть пустым!{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Начинаем сканирование всей системы...{Colors.RESET}\n")
    start_time = time.time()
    
    scanner = FileScanner(extension, max_workers=16)  
    
    try:
        found_files = scanner.scan_system()
        
        # Вывод результатов
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}     РЕЗУЛЬТАТЫ ПОИСКА{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        
        print(f"{Colors.CYAN}Расширение: .{extension}{Colors.RESET}")
        print(f"{Colors.CYAN}Найдено файлов: {len(found_files)}{Colors.RESET}")
        print(f"{Colors.CYAN}Время выполнения: {elapsed_time:.2f} секунд{Colors.RESET}")
        
        if found_files:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}Список найденных файлов:{Colors.RESET}\n")
            for i, file in enumerate(found_files, 1):
                print(f"{Colors.GREEN}{i}. {file}{Colors.RESET}")
            

            save_option = input(f"\n{Colors.YELLOW}Сохранить результаты в файл? (y/n): {Colors.RESET}").lower()
            if save_option == 'y':
                output_file = f"found_files_{extension}_{int(time.time())}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Поиск файлов с расширением .{extension}\n")
                    f.write(f"Найдено файлов: {len(found_files)}\n")
                    f.write("="*60 + "\n\n")
                    for file in found_files:
                        f.write(f"{file}\n")
                print(f"{Colors.GREEN}Результаты сохранены в файл: {output_file}{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}Файлы с расширением .{extension} не найдены{Colors.RESET}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Сканирование прервано пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Произошла ошибка: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()