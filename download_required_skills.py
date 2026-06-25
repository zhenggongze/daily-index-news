import urllib.request
import zipfile
import os
import shutil

def download_and_extract_github_repo(repo_url, dest_dir, repo_name):
    zip_path = f'{repo_name}-repo.zip'
    
    print(f'正在下载 {repo_name}...')
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(repo_url, zip_path)
    print(f'{repo_name} 下载完成！')
    
    print(f'正在解压 {repo_name}...')
    temp_extract = f'temp-{repo_name}'
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)
    print(f'{repo_name} 解压完成！')
    
    extracted_files = os.listdir(temp_extract)
    repo_dir = os.path.join(temp_extract, extracted_files[0])
    
    final_dest = os.path.join(dest_dir, repo_name)
    if os.path.exists(final_dest):
        shutil.rmtree(final_dest)
    shutil.copytree(repo_dir, final_dest)
    
    print(f'✓ {repo_name} 已安装到 {final_dest}')
    
    os.remove(zip_path)
    shutil.rmtree(temp_extract)

def main():
    dest_dir = 'skills-new'
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    print('=' * 60)
    print('开始下载所需技能')
    print('=' * 60)
    
    try:
        download_and_extract_github_repo(
            'https://github.com/OthmanAdi/planning-with-files/archive/refs/heads/main.zip',
            dest_dir,
            'planning-with-files'
        )
    except Exception as e:
        print(f'✗ planning-with-files 下载失败: {e}')
    
    try:
        download_and_extract_github_repo(
            'https://github.com/Liu-PenPen/skill-review/archive/refs/heads/main.zip',
            dest_dir,
            'code-review'
        )
    except Exception as e:
        print(f'✗ code-review 下载失败: {e}')
    
    try:
        download_and_extract_github_repo(
            'https://github.com/anthropics/claude-plugins-official/archive/refs/heads/main.zip',
            dest_dir,
            'claude-plugins-official'
        )
        
        plugin_dir = os.path.join(dest_dir, 'claude-plugins-official', 'plugins', 'code-simplifier')
        if os.path.exists(plugin_dir):
            final_dest = os.path.join(dest_dir, 'code-simplifier')
            if os.path.exists(final_dest):
                shutil.rmtree(final_dest)
            shutil.copytree(plugin_dir, final_dest)
            print(f'✓ code-simplifier 已提取到 {final_dest}')
            shutil.rmtree(os.path.join(dest_dir, 'claude-plugins-official'))
        else:
            print('✗ code-simplifier 未在 claude-plugins-official 中找到')
    except Exception as e:
        print(f'✗ code-simplifier 下载/提取失败: {e}')
    
    print('\n' + '=' * 60)
    print('下载任务完成！')
    print('=' * 60)

if __name__ == '__main__':
    main()
