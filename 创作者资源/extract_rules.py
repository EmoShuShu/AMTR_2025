import requests
from bs4 import BeautifulSoup
import re

def discover_all_page_urls(main_url):
    """
    从主页面 https://blogs.magicjudges.org/rules/mtr/ 发现所有规则条款的链接。
    """
    urls = set()
    print(f"正在从主页面 <{main_url}> 查找所有规则链接...")

    try:
        response = requests.get(main_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 使用一个宽容的正则表达式来捕获所有符合条件的链接
        # 匹配所有包含 /rules/mtr<数字>-<数字> 格式的链接
        for link in soup.find_all('a', href=re.compile(r'/rules/mtr\d+-\d+')):
            href = link.get('href')
            if href:
                # 确保URL是完整的
                if not href.startswith('http'):
                    href = requests.compat.urljoin(main_url, href)
                urls.add(href)

    except requests.exceptions.RequestException as e:
        print(f"错误: 访问主页面 {main_url} 失败: {e}")
        return []

    if not urls:
        print("警告: 未能在主页面上找到任何符合 '/rules/mtrX-Y' 格式的链接。")
        return []
    
    return list(urls) # 返回列表，之后再排序

def extract_info_from_url(url):
    """
    从给定的URL中提取所有class="alert alert-info"的div中的纯文本。
    """
    extracted_texts = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        info_divs = soup.find_all('div', class_='alert alert-info', role='alert')
        for div in info_divs:
            text = div.get_text(strip=True)
            if text:
                extracted_texts.append(text)
            
    except requests.exceptions.RequestException as e:
        print(f"  -> 警告: 处理页面 {url} 时出错: {e}")
    return extracted_texts

def get_natural_sort_key(url):
    """
    为URL生成一个用于自然排序的键。
    例如，从 '.../mtr10-2/' 中提取出 (10, 2)。
    """
    # 使用正则表达式匹配并捕获章节号和条款号
    match = re.search(r'mtr(\d+)-(\d+)', url)
    if match:
        # 将捕获到的字符串转换为整数，并返回一个元组
        chapter = int(match.group(1))
        section = int(match.group(2))
        return (chapter, section)
    # 如果URL格式不匹配，返回一个很大的元组，使其排在最后
    return (999, 999)

# --- 主程序 ---
if __name__ == "__main__":
    main_page_url = 'https://blogs.magicjudges.org/rules/mtr/'
    output_filename = 'extracted_rules.txt'
    
    # 第一步: 发现所有相关的URL
    rule_urls = discover_all_page_urls(main_page_url)
    
    if not rule_urls:
        print("程序终止，因为未能发现任何可处理的URL。")
    else:
        print(f"发现 {len(rule_urls)} 个规则页面。开始提取信息...")
        print("-" * 50)
        
        all_extracted_data = {}
        
        # 第二步: 遍历URL，提取信息
        for i, url in enumerate(rule_urls):
            print(f"正在处理: [{i+1}/{len(rule_urls)}] {url}")
            texts = extract_info_from_url(url)
            if texts:
                all_extracted_data[url] = texts
        
        print("\n" + "=" * 50)
        print("所有页面处理完毕！")
        
        # 第三步: 将结果按要求格式化并写入文件
        if not all_extracted_data:
            print("在所有找到的子页面中，均未提取到任何目标信息。")
        else:
            print(f"正在将 {len(all_extracted_data)} 个页面的结果按章节排序并写入文件: {output_filename}")
            
            # **优化点 2: 使用自定义函数对URL进行自然排序**
            sorted_urls = sorted(all_extracted_data.keys(), key=get_natural_sort_key)
            
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    for url in sorted_urls:
                        texts = all_extracted_data[url]
                        
                        # **优化点 1: 提取并简化章节标题**
                        header_match = re.search(r'mtr\d+-\d+', url)
                        simple_header = header_match.group(0) if header_match else url
                        
                        f.write(f"--- {simple_header} ---\n")
                        for i, text in enumerate(texts):
                            f.write(f"[{i+1}]: {text}\n")
                        f.write("\n")
                print(f"成功！所有提取内容已保存至 {output_filename}")
            except IOError as e:
                print(f"错误: 写入文件失败: {e}")