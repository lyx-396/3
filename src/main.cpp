#include "dictionary.h"

#include <iostream>
#include <sstream>

namespace {
void showMenu() {
    std::cout << "\n===== 中英文词典管理系统 =====" << std::endl;
    std::cout << "1. 输入批量单词信息" << std::endl;
    std::cout << "2. 显示所有单词" << std::endl;
    std::cout << "3. 插入单词" << std::endl;
    std::cout << "4. 删除单词" << std::endl;
    std::cout << "5. 修改单词" << std::endl;
    std::cout << "6. 精准查询" << std::endl;
    std::cout << "7. 模糊查询" << std::endl;
    std::cout << "8. 导出首字母为 a/c/e/f 的单词" << std::endl;
    std::cout << "9. 显示多个单词信息" << std::endl;
    std::cout << "0. 退出" << std::endl;
    std::cout << "请选择操作：";
}

WordEntry readEntryFromUser() {
    WordEntry entry;
    std::cout << "请输入英文单词：";
    std::getline(std::cin, entry.english);
    std::cout << "请输入词性：";
    std::getline(std::cin, entry.partOfSpeech);
    std::cout << "请输入中文词意：";
    std::getline(std::cin, entry.chinese);
    return entry;
}

} // namespace

int main() {
    const std::string dictionaryFile = "data/dictionary.txt";
    Dictionary dictionary(dictionaryFile);

    while (true) {
        showMenu();
        std::string choice;
        if (!std::getline(std::cin, choice)) {
            break;
        }

        if (choice == "1") {
            std::cout << "请输入需要录入的单词数量(不少于50)：";
            std::string countStr;
            std::getline(std::cin, countStr);
            std::size_t count = std::stoul(countStr);
            dictionary.inputEntries(count);
        } else if (choice == "2") {
            dictionary.displayAll();
        } else if (choice == "3") {
            WordEntry entry = readEntryFromUser();
            dictionary.insertEntry(entry);
            std::cout << "单词插入成功。" << std::endl;
        } else if (choice == "4") {
            std::cout << "请输入要删除的英文单词：";
            std::string word;
            std::getline(std::cin, word);
            if (dictionary.deleteEntry(word)) {
                std::cout << "删除成功。" << std::endl;
            } else {
                std::cout << "未找到对应的单词。" << std::endl;
            }
        } else if (choice == "5") {
            std::cout << "请输入要修改的英文单词：";
            std::string word;
            std::getline(std::cin, word);
            WordEntry newEntry = readEntryFromUser();
            newEntry.english = word;
            if (dictionary.modifyEntry(word, newEntry)) {
                std::cout << "修改成功。" << std::endl;
            } else {
                std::cout << "未找到对应的单词。" << std::endl;
            }
        } else if (choice == "6") {
            std::cout << "请输入要查询的英文单词：";
            std::string word;
            std::getline(std::cin, word);
            auto results = dictionary.queryExact(word);
            dictionary.displayEntries(results);
        } else if (choice == "7") {
            std::cout << "请输入模糊查询关键字：";
            std::string pattern;
            std::getline(std::cin, pattern);
            auto results = dictionary.queryFuzzy(pattern);
            dictionary.displayEntries(results);
        } else if (choice == "8") {
            const std::string outputFile = "data/dictionary_acef.txt";
            dictionary.exportByInitials({'a', 'c', 'e', 'f'}, outputFile);
            std::cout << "导出完成，文件路径：" << outputFile << std::endl;
        } else if (choice == "9") {
            std::cout << "请输入要同时显示的英文单词，使用逗号分隔：";
            std::string input;
            std::getline(std::cin, input);
            std::vector<WordEntry> collected;
            std::istringstream iss(input);
            std::string word;
            while (std::getline(iss, word, ',')) {
                auto entries = dictionary.queryExact(word);
                collected.insert(collected.end(), entries.begin(), entries.end());
            }
            dictionary.displayEntries(collected);
        } else if (choice == "0") {
            break;
        } else {
            std::cout << "无效的选择，请重新输入。" << std::endl;
        }
    }

    std::cout << "感谢使用中英文词典系统。" << std::endl;
    return 0;
}
