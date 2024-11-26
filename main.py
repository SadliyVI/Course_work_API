import threading
import json
from tkinter.ttk import Progressbar
import requests
from tkinter import *
from tkinter import  messagebox
import datetime
import configparser


# 1. Класс для работы с API VK
# 1. Class for working with VK API


class VKAPIClient:
    """
        A class to interact with the VK API.

        Attributes:
            API_BASE_URL (str): The base URL for VK API methods.
            access_token (str): The access token for VK API.
            user_id (int): The ID of the VK user.
            version (str): The version of the VK API.
    """

    API_BASE_URL = 'https://api.vk.com/method/'


    @staticmethod
    def write_result_to_json(photo_set: list[dict]):
        """
        Write the photo set to a JSON file.

        Args:
            photo_set (list[dict]): A list of dictionaries containing photo
            information.

        Returns:
            None
        """
        with open(r'files\result.json', 'w', encoding='utf-8') as f:
            json.dump(photo_set, f, indent=2)

    @staticmethod
    def read_result_from_json() -> list[dict]:
        """
        Read the photo set from a JSON file.

        Returns:
            list[dict]: A list of dictionaries containing photo information.
        """
        with open(r'files\result.json', encoding='utf-8') as f:
            data = json.load(f)
            return data

    def __init__(self, user_id: int, access_token: str,
                 version: str = '5.199'):
        """
        Initialize the VKAPIClient.

        Args:
            user_id (int): The ID of the VK user.
            access_token (str): The access token for the VK API.
            version (str, optional): The version of the VK API. Defaults to '5.199'.
        """
        self.access_token = access_token
        self.user_id = user_id
        self.version = version

    def get_common_params(self) -> dict:
        """
        Get common parameters for API requests.

        Returns:
            dict: A dictionary containing common parameters for API requests.
        """
        return {
            'access_token': self.access_token,
            'v': self.version
        }

    def _build_url(self, api_method: str) -> str:
        """
        Build the full URL for an API method.

        Args:
            api_method (str): The API method to be called.

        Returns:
            str: The full URL for the API method.
        """
        return f'{self.API_BASE_URL}/{api_method}'

    def get_profile_photos_set(self) -> list[tuple[int, dict]]:
        """
        Retrieve the set of profile photos for the user.

        Returns:
            list[tuple[int, dict]]: A list of tuples, where each tuple contains
            the photo ID (int) and a dictionary of photo details.
            Returns an empty dictionary if there's an error.
        """
        params = self.get_common_params()
        params.update({'owner_id': self.user_id, 'album_id': 'profile',
                       'extended': 1, 'photo_sizes': 1})
        try:
            response = requests.get(self._build_url('photos.get'),
                                    params = params)
            response.raise_for_status()
        except requests.RequestException as e:
            messagebox.showerror(message = f'Ошибка соединения: {e}')
            return []
        response_json = response.json()
        if 'error' in response_json:
            messagebox.showerror(message = response_json['error']['error_msg'])
            return []
        photo_set = {}
        for photo in response_json['response']['items']:
            photo_set[photo['id']] = {}
            for _ in photo:
                photo_set[photo['id']]['likes'] = photo['likes']['count']
                photo_set[photo['id']]['date'] = photo['date']
                photo_set[photo['id']]['height'] = photo['sizes'][-1][
                    'height']
                photo_set[photo['id']]['width'] = photo['sizes'][-1][
                    'width']
                photo_set[photo['id']]['size_type'] = photo['sizes'][
                    -1]['type']
                photo_set[photo['id']]['url'] = photo['sizes'][-1]['url']
        photo_set = list(photo_set.items())
        return photo_set


# 2. Класс для работы с API ЯндексДиска
# 2. Class for working with Yandex Disk API


class APIYaDiClient:
    """
    A class to interact with the Yandex Disk API.

    Attributes:
        BASE_API_YADI_URL (str): The base URL for Yandex Disk API methods.
        token (str): The access token for Yandex Disk API.
        upload_counter (int): The counter for uploaded files.
        same_id_list (list): A list to store IDs of photos with the same likes.
    """

    BASE_API_YADI_URL = 'https://cloud-api.yandex.net/v1/disk/resources'

    def __init__(self, token: str):
        """
        Initialize the APIYaDiClient.

        Args:
            token (str): The access token for Yandex Disk API.
        """
        self.token = token
        self.upload_counter = 0
        self.same_id_list = []
    @staticmethod
    def get_base_params() -> dict:
        """
        Get base parameters for API requests.

        Returns:
            dict: A dictionary containing base parameters for API requests.
        """
        return {}

    @staticmethod
    def get_base_headers() -> dict:
        """
        Get base headers for API requests.

        Returns:
            dict: A dictionary containing base headers for API requests.
        """
        return {
            'Content-Type': 'application/json'
        }

    def create_directory(self, dir_name: str) -> int:
        """
        Create a directory on Yandex Disk.

        Args:
            dir_name (str): The name of the directory to be created.

        Returns:
            int: The status code of the request.
        """
        headers = self.get_base_headers()
        headers.update({'Authorization': f'OAuth {yadi_token}'})
        params = self.get_base_params()
        params['path'] = dir_name
        response = requests.put(self.BASE_API_YADI_URL, params = params,
                                headers = headers)
        status = response.status_code
        request_info = response.json()
        if status == 201:
            messagebox.showinfo(f'Статус запроса: {status}',
                                message = 'Папка успешно создана')
            return status
        elif status == 409:
            messagebox.showinfo(f'Статус запроса: {status}',
                                message = 'Папка уже существует')
            return status
        else:
            messagebox.showerror(f'Код ошибки: {status}',
                             message = request_info['message'])
            return status

    @staticmethod
    def get_date(publication_date: int) -> str:
        """
        Convert a Unix timestamp to a date string.

        Args:
            publication_date (int): The Unix timestamp.

        Returns:
            str: The date in the format 'YYYY-MM-DD'.
        """
        return (datetime.datetime.fromtimestamp(publication_date).
                strftime('%Y-%m-%d'))

    def get_equal_likes_id(self, data_list: list[tuple], number: int):
        """
        Find and store in object's parameter IDs of photos with the same
        number of likes.

        Args:
            data_list (list[tuple]): A list of tuples containing photo data.
            number (int): The number of photos to check.
        """
        for i in range(number - 1):
            j = i
            while j != number - 1:
                if data_list[i][1]['likes'] == data_list[j + 1][1][
                    'likes']:
                    if data_list[i][0] not in self.same_id_list:
                        self.same_id_list.append(data_list[i][0])
                    if data_list[j + 1][0] not in self.same_id_list:
                        self.same_id_list.append(data_list[j + 1][0])
                j += 1

    @staticmethod
    def get_filename(photo_id_list: list, photo_data: tuple) -> str:
        """
        Generate a filename based on the photo's likes and date of download.

        Args:
            photo_id_list (list): A list of photo IDs.
            photo_data (tuple): A tuple containing photo data.

        Returns:
            str: The generated filename.
        """
        if photo_data[0] in photo_id_list:
            filename = (f'{photo_data[1]['likes']}_'
                        f'{APIYaDiClient.get_date(photo_data[1]['date'])}')
            return filename
        else:
            filename = f'{photo_data[1]['likes']}'
            return filename

    @staticmethod
    def get_file_extension(url_string: str) -> str:
        """
        Extract the file extension from a URL.

        Args:
            url_string (str): The URL of the file.

        Returns:
            str: The file extension.
        """
        return url_string.rpartition('?')[0].rpartition('.')[2]

    def upload_photo(self, photo_data_list: list[tuple], item_number: int,
                     directory_name: str):
        """
        Upload photos to Yandex Disk.

        Args:
            photo_data_list (list[tuple]): A list of tuples containing photo data.
            item_number (int): The number of photos to upload.
            directory_name (str): The name of the directory to upload to.

        Returns:
            list: A list of dictionaries containing upload results.
        """
        request_app.create_progressbar(item_number)
        status = self.create_directory(directory_name)
        if status == 201 or status == 409:
            headers = self.get_base_headers()
            headers.update({'Authorization': f'OAuth {yadi_token}'})
            params = self.get_base_params()
            self.get_equal_likes_id(photo_data_list, item_number)
            request_url  = f'{self.BASE_API_YADI_URL}/upload'
            result_report = []
            for item in photo_data_list[:item_number]:
                filename = self.get_filename(self.same_id_list, item)
                file_extension = self.get_file_extension(item[1]['url'])
                params['path'] = (f'{directory_name}/{filename}'
                                  f'.{file_extension}')
                params['url'] = item[1]['url']
                try:
                    response = requests.post(request_url, params = params,
                                     headers = headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    messagebox.showerror(title = 'Ошибка загрузки',
                                         message = f'Ошибка загрузки '
                                                   f'фотографии: {e}')
                    return []
                self.upload_counter += 1
                status = response.status_code
                result_report.append({'file_name': f'{filename}.{file_extension}',
                                          'size': item[1]['size_type']})
                request_app.start_progressbar(self.upload_counter, item_number)
            VKAPIClient.write_result_to_json(result_report)
            request_app.stop_progressbar()
            return result_report
        else:
            return messagebox.showerror('Ошибка создания директории!')


# 3. Класс для работы с графическим интерфейсом
# 3. Class for working with the graphical user interface


class GUIRequestApplication:
    """
    A class to manage the graphical user interface for the application.

    Attributes:
        root (Tk): The root window of the application.
        user_id_entry (str): The entry field for the user ID.
        token_entry (str): The entry field for the access token.
        photo_number_entry (str): The entry field for the number of photos.
        resourse_name_entry (str): The entry field for the directory name.
        photo_data_list (list): A list of photo data.
        photo_counter (int): The counter for photos.
        progressbar (Progressbar): The progress bar widget.
        message_text (StringVar): The text variable for the progress message.
    """

    def __init__(self, root: Tk):
        """
           Initialize the GUIRequestApplication.

           Args:
               root (Tk): The root window of the application.
           """
        self.root = root
        self.root.title('Резервная копия фотографий профиля VK')
        self.root.iconbitmap(r'resourses/icon-sm-gru.ico')
        self.root.geometry('450x130')
        self.root.resizable(width = False, height = False)
        self.root['bg'] = 'blue'
        self.user_id_entry = ''
        self.token_entry = ''
        self.photo_number_entry = ''
        self.resourse_name_entry = ''
        self.photo_data_list = []
        self.photo_counter = 0
        self.create_widgets()
        self.progressbar = None
        self.message_text = ''


    def send_request(self):
        """
        Send a request to retrieve  profile photos data from VK.

        Returns:
            None
        """
        user_id = self.user_id_entry.get()
        if user_id.isdigit():
            user_id = int(user_id)
        else:
            return messagebox.showerror(message = 'Ошибка ввода ID '
                                                  'пользователя!')
        token = yadi_token
        if token:
            vk_client = VKAPIClient(user_id, vk_token)
            photo_set = vk_client.get_profile_photos_set()
            if photo_set:
                self.root.geometry('450x330')
                self.show_responce_result(photo_set)
                self.photo_data_list = photo_set
            elif photo_set == []:
                 messagebox.showinfo(message = 'У пользователя нет '
                                               'фотографий!')
        else:
            messagebox.showerror(message = 'Ошибка ввода токена!')


    def create_widgets(self):
        """
        Create the widgets for the graphical user interface.

        Returns:
            None
        """
        self.user_id_label = Label(self.root, text = 'ID пользователя в VK',
                                   font = 'Arial 11 bold', bg = 'blue',
                                   fg = 'white', padx = 10, pady = 10)
        self.user_id_label.pack()

        self.user_id_entry = Entry(self.root, font = 'Arial 12',
                                   bg = 'lightblue', fg = 'black', width = 12)
        self.user_id_entry.pack()

        self.send_btn = Button(self.root, text ='Отправить запрос',
                               font = 'Arial 10 bold',
                               command = self.send_request, foreground = 'blue')
        self.send_btn.pack(padx = 10, pady = 20)

    def show_responce_result(self, responce_result: list[tuple]):
        """
        Display the result of the request.

        Args:
            responce_result (list[tuple]): The result of the request.

        Returns:
            None
        """
        if responce_result:
            self.photo_counter = len(responce_result)

            label_text = (f'В альбоме профиля {self.photo_counter} '
                             f'фотографий.\nСколько фотографий загрузить '
                             f'на Яндекс.Диск?')
            self.responce_label = Label(self.root, text=label_text,
                                        font='Arial 10 bold', bg='blue',
                                        fg='white', padx=10, pady=10)
            self.responce_label.pack()

            self.photo_number_entry = Entry(self.root, font = 'Arial 12',
                                            bg = 'lightblue', fg = 'black',
                                            width = 5)
            self.photo_number_entry.pack()

            self.resourse_name_label = Label(self.root, text = 'Введите имя '
                                             'папки', font='Arial 10 bold',
                                             bg='blue', fg='white',
                                             padx=10, pady=10)
            self.resourse_name_label.pack()

            self.resourse_name_entry = Entry(self.root, font = 'Arial 12',
                                             bg = 'lightblue', fg = 'black',
                                             width = 30)
            self.resourse_name_entry.pack()

            self.upload_btn = Button(self.root, text = 'Загрузить',
                                     font = 'Arial 10 bold',
                                     foreground = 'blue',
                                     command = self.start_upload_photo)
            self.upload_btn.pack(padx = 10, pady = 10)

    def start_upload_photo(self):
        """
        Start the photo upload process and creates a separate thread for
        downloading photo

        Returns:
            None
        """
        item_number = self.photo_number_entry.get()
        if item_number and item_number.isdigit():
            item_number = int(item_number)
            if item_number <= self.photo_counter:
                resourse_name = self.resourse_name_entry.get()
                if resourse_name == '':
                    messagebox.showerror(message = 'Поле с названием '
                                                   'директории\nне должно быть пустым!')
                else:
                    self.root.geometry('450x430')
                    yadi_client = APIYaDiClient(yadi_token)
                    self.thread = threading.Thread(target =
                                                   yadi_client.upload_photo,
                                                   args=(
                                                       self.photo_data_list,
                                                       item_number,
                                                       resourse_name
                                                   ))
                    self.thread.start()
            else:
                messagebox.showerror(message = 'Количество фотографий больше '
                                               'чем в альбоме!')
        else:
            messagebox.showerror(message='Проверьте правильность заполнения '
                                 'поля с количеством фотографий!')

    def create_progressbar(self, value: int):
        """
        Create a progress bar widget.

        Args:
            value (int): The maximum value of the progress bar.

        Returns:
            Progressbar: The created progress bar widget.
        """
        self.message_text = StringVar()

        num_label = Label(self.root, font = 'Arial 10 bold',
                          textvariable = self.message_text,
                          bg = 'blue', fg = 'white', padx = 10, pady = 10)
        num_label.pack()

        self.progressbar = Progressbar(self.root, orient = HORIZONTAL,
                                       length=300, mode = 'determinate',
                                       maximum = value)
        self.progressbar.pack(pady = 10)

        return self.progressbar

    def start_progressbar(self, progress: int, counter: int):
        """
        Update the progress bar.

        Args:
            progress (int): The current progress.
            counter (int): The total number of items.

        Returns:
            None
        """
        self.progressbar['value'] = progress
        self.message_text.set(f'Загружено {self.progressbar['value']} из'
                              f' {counter} фотографий')
        self.root.update_idletasks()

    def stop_progressbar(self):
        """
        Stop and clean up the progress bar and GUI

        Returns:
            None
        """
        self.root.geometry('450x240')
        self.progressbar.destroy()
        self.photo_number_entry.destroy()
        self.resourse_name_entry.destroy()
        self.resourse_name_label.destroy()
        self.responce_label.destroy()
        self.upload_btn.destroy()
        self.send_btn.destroy()
        self.message_text.set('Загрузка завершена!')

        result_json_btn = Button(self.root, text = 'Просмотреть\nрезультат',
                                font = 'Arial 10 bold', foreground = 'blue',
                                command = self.get_upload_result)
        result_json_btn.pack(padx = 10, pady = 10)

        close_button = Button(self.root, text = 'Завершить работу?',
                              font = 'Arial 10 bold', foreground = 'blue',
                              command = lambda: self.root.destroy())
        close_button.pack(side = 'bottom', padx = 20, pady = 10)

    @staticmethod
    def get_upload_result():
        """
        Display the upload result in a new window.

        Returns:
            None
        """
        window = Tk()
        window.title('Результат загрузки')
        window.geometry('450x400')

        close_button = Button(window, text = 'Закрыть окно',
                              command = lambda: window.destroy())
        close_button.pack(side = 'bottom')

        text_area = Text(window, width = 100, height = 50, font = 'Arial 12')
        text_area.pack()

        try:
            with open(r'files/result.json', 'r', encoding = 'utf-8') as f:
                data = json.load(f)
                text_area.delete('1.0', END)
                text_area.insert(INSERT, str(data))
        except FileNotFoundError:
            messagebox.showerror(message = 'Файл не найден')
        except json.JSONDecodeError:
            messagebox.showerror(message = 'Невозможно декодировать JSON')

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(r'files/settings.ini')
    vk_token = config['Tokens']['vk_token']
    yadi_token = config['Tokens']['yadi_token']
    root = Tk()
    request_app = GUIRequestApplication(root)
    root.mainloop()





