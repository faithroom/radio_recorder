import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile
from pathlib import PurePath

class GoogleDriveControl:
    
    def __init__(self, setting_path: str='google_drive.yaml'):
        gauth = GoogleAuth(setting_path)
        gauth.LocalWebserverAuth()

        self.drive = GoogleDrive(gauth)

    # 指定したフォルダをサーチして ID を返す
    def search_folder(self, path, parent_id='root'):
        folders = path.split('/')

        try:
            for index, folder_name in enumerate(folders):
                query = '"{}" in parents and trashed=false'.format(parent_id)
                file_list = self.drive.ListFile({'q': query})

                next_id = ''
                for file in file_list.GetList():
                    if file['mimeType'] == 'application/vnd.google-apps.folder' and file['title'] == folder_name:
                        next_id = file['id']
                        break
                if next_id == '':
                    folder = self.create_folder(folder_name, parent_id)
                    parent_id = folder["id"]
                else:
                    parent_id = next_id

        except:
            return false
            pass

        return parent_id

    # drive_folder_id 以下の指定ファイルをダウンロード
    def download(self, drive_folder_id, file_name):
        max_results = 1000
        query = "'{}' in parents and trashed=false".format(drive_folder_id)

        for file_list in self.drive.ListFile({'q': query, 'maxResults': max_results}):
            for file in file_list:
                if file['title'] == file_name:
                    return file.GetContentString()

    # drive_folder_id 以下のファイルを再帰的にダウンロードして save_folder に保存
    def download_recursively(self, save_folder, drive_folder_id):
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        max_results = 1000
        query = "'{}' in parents and trashed=false".format(drive_folder_id)

        for file_list in self.drive.ListFile({'q': query, 'maxResults': max_results}):
            for file in file_list:
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    download_recursively(os.path.join(save_folder, file['title']), file['id'])
                else:
                    file.GetContentFile(os.path.join(save_folder, file['title']))
                    print('Download {}'.format(file['title']))

    # 全ドライブからファイル名でサーチしてリストアップ
    def list_files(self, folder_name):
        query = f'title = "{os.path.basename(folder_name)}"'

        list = self.drive.ListFile({'q': query}).GetList()
        if len(list) > 0:
            return list[0]
        return False

    # 指定した名前でフォルダを作成
    def create_folder(self, folder_name, parent_id='root'):
        ret = self.list_files(folder_name)
        if ret:
            folder = ret
            print(f"{folder['title']}: exists")
        else:   
            folder = self.drive.CreateFile(
                {
                    'title': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [
                        {'id': parent_id}
                    ]
                }
            )
            folder.Upload()

        return folder

    # ファイル名を変更
    def rename_file(self, file_id: str, new_name: str) -> GoogleDriveFile:
        # file = self.download_file(file_id)
        file = self.drive.CreateFile({"id": file_id})
        file.FetchMetadata()  # メタデータを最新の状態へ更新
        file["title"] = new_name
        file.Upload()
        return file

    # ファイルを指定名のフォルダにアップロード
    def upload_folder_with_name(self, local_file_path: str, save_folder_name: str):
        if save_folder_name:
            folder = self.create_folder(save_folder_name)

        return self.upload(local_file_path, folder["id"])

    # ファイルを指定 ID のフォルダにアップロード
    def upload(self, local_file_path: str, save_folder_id: str):
        file_name = PurePath(local_file_path).name
        self.delete(file_name, save_folder_id)

        file = self.drive.CreateFile(
            {
                'title':os.path.basename(local_file_path),
                'parents': [
                    {'id': save_folder_id}
                ]
            }
        )

        file.SetContentFile(local_file_path)
        file.Upload({'convert': False})
        
        drive_url = f"https://drive.google.com/uc?id={str( file['id'] )}"
        file = self.rename_file(file["id"], file_name)
        print("Gdrive upload", file['title'])

        return drive_url

    # 与えた内容のファイルを指定 ID のフォルダ、ファイル名にアップロード
    def upload_content(self, save_folder_id: str, file_name: str, content: str):
        self.delete(file_name, save_folder_id)
        file = self.drive.CreateFile(
            {
                'title':file_name,
                'parents': [
                    {'id': save_folder_id}
                ]
            }
        )
        file.SetContentString(content)
        file.Upload()


    # 指定フォルダ ID, ファイル名のファイルを完全削除
    def delete(self, file_name: str, folder_id: str):
        query = f'"{folder_id}" in parents and title = "{file_name}"'
        list = self.drive.ListFile({'q': query}).GetList()
        for file in list:
            file.Delete()

    # ゴミ箱を空に
    def clear_trash(self):
        trash_list = self.drive.ListFile({'q': "trashed=true"}).GetList()
        for file in trash_list:
            file.Delete()

    # 指定フォルダのファイル一覧を取得
    def get_file_list(self, folder_id):
        if folder_id:
            file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
            return [file['title'] for file in file_list]
