#include "dictionary.h"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>

namespace {
std::string trim(const std::string &value) {
    auto start = value.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return "";
    }
    auto end = value.find_last_not_of(" \t\r\n");
    return value.substr(start, end - start + 1);
}

std::string toLower(const std::string &value) {
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return result;
}

} // namespace

Dictionary::Dictionary(const std::string &dictionaryFilePath)
    : dictionaryFilePath_(dictionaryFilePath) {
    loadFromFile();
}

Dictionary::~Dictionary() {
    clearList();
}

void Dictionary::clearList() {
    Node *current = head_;
    while (current != nullptr) {
        Node *next = current->next;
        delete current;
        current = next;
    }
    head_ = nullptr;
}

void Dictionary::rebuildListFromArray() {
    clearList();
    for (const auto &entry : entriesArray_) {
        insertIntoListSorted(entry);
    }
}

void Dictionary::insertIntoListSorted(const WordEntry &entry) {
    Node *newNode = new Node{entry, nullptr};
    if (head_ == nullptr || toLower(entry.english) < toLower(head_->entry.english)) {
        newNode->next = head_;
        head_ = newNode;
        return;
    }

    Node *current = head_;
    while (current->next != nullptr && toLower(current->next->entry.english) < toLower(entry.english)) {
        current = current->next;
    }
    newNode->next = current->next;
    current->next = newNode;
}

void Dictionary::loadFromFile() {
    entriesArray_.clear();
    clearList();

    std::ifstream input(dictionaryFilePath_);
    if (!input.is_open()) {
        return;
    }

    std::string line;
    while (std::getline(input, line)) {
        if (line.empty()) {
            continue;
        }
        std::istringstream iss(line);
        std::string english;
        std::string partOfSpeech;
        std::string chinese;

        if (!std::getline(iss, english, '\t')) {
            continue;
        }
        if (!std::getline(iss, partOfSpeech, '\t')) {
            continue;
        }
        if (!std::getline(iss, chinese)) {
            continue;
        }

        WordEntry entry{trim(english), trim(partOfSpeech), trim(chinese)};
        if (!entry.english.empty()) {
            entriesArray_.push_back(entry);
            insertIntoListSorted(entry);
        }
    }
}

void Dictionary::saveToFile() const {
    std::filesystem::create_directories(std::filesystem::path(dictionaryFilePath_).parent_path());
    std::ofstream output(dictionaryFilePath_, std::ios::trunc);
    Node *current = head_;
    while (current != nullptr) {
        output << current->entry.english << '\t'
               << current->entry.partOfSpeech << '\t'
               << current->entry.chinese << '\n';
        current = current->next;
    }
}

void Dictionary::inputEntries(std::size_t count) {
    if (count < 50) {
        std::cout << "输入的单词数量必须不少于50个。" << std::endl;
        return;
    }

    std::set<char> initialsPresent;
    for (std::size_t i = 0; i < count; ++i) {
        WordEntry entry;
        std::cout << "请输入第" << (i + 1) << "个单词的英文：";
        std::getline(std::cin, entry.english);
        entry.english = trim(entry.english);
        if (entry.english.empty()) {
            std::cout << "英文单词不能为空，请重新输入。" << std::endl;
            --i;
            continue;
        }
        std::cout << "请输入该单词的词性：";
        std::getline(std::cin, entry.partOfSpeech);
        entry.partOfSpeech = trim(entry.partOfSpeech);
        std::cout << "请输入该单词的中文词意：";
        std::getline(std::cin, entry.chinese);
        entry.chinese = trim(entry.chinese);

        entriesArray_.push_back(entry);
        insertIntoListSorted(entry);

        if (!entry.english.empty()) {
            initialsPresent.insert(static_cast<char>(std::tolower(static_cast<unsigned char>(entry.english.front()))));
        }
    }

    const std::set<char> requiredInitials = {'a', 'b', 'c', 'd', 'e', 'f'};
    if (!std::includes(initialsPresent.begin(), initialsPresent.end(), requiredInitials.begin(), requiredInitials.end())) {
        std::cout << "警告：输入的单词没有覆盖所有要求的首字母 (a, b, c, d, e, f)。" << std::endl;
    }

    saveToFile();
}

void Dictionary::displayAll() const {
    std::cout << "按字典序排列的单词列表：" << std::endl;
    Node *current = head_;
    int index = 1;
    while (current != nullptr) {
        std::cout << index++ << ". " << current->entry.english << " [" << current->entry.partOfSpeech
                  << "] - " << current->entry.chinese << std::endl;
        current = current->next;
    }
}

void Dictionary::insertEntry(const WordEntry &entry) {
    entriesArray_.push_back(entry);
    insertIntoListSorted(entry);
    saveToFile();
}

bool Dictionary::deleteEntry(const std::string &englishWord) {
    std::string target = toLower(englishWord);
    auto it = std::remove_if(entriesArray_.begin(), entriesArray_.end(), [&](const WordEntry &entry) {
        return toLower(entry.english) == target;
    });
    if (it == entriesArray_.end()) {
        return false;
    }
    entriesArray_.erase(it, entriesArray_.end());

    Node *current = head_;
    Node *prev = nullptr;
    bool removed = false;
    while (current != nullptr) {
        if (toLower(current->entry.english) == target) {
            Node *toDelete = current;
            if (prev == nullptr) {
                head_ = current->next;
            } else {
                prev->next = current->next;
            }
            current = current->next;
            delete toDelete;
            removed = true;
        } else {
            prev = current;
            current = current->next;
        }
    }

    if (removed) {
        saveToFile();
    }
    return removed;
}

bool Dictionary::modifyEntry(const std::string &englishWord, const WordEntry &updatedEntry) {
    std::string target = toLower(englishWord);
    bool updated = false;
    for (auto &entry : entriesArray_) {
        if (toLower(entry.english) == target) {
            entry = updatedEntry;
            updated = true;
        }
    }

    if (!updated) {
        return false;
    }

    rebuildListFromArray();
    saveToFile();
    return true;
}

std::vector<WordEntry> Dictionary::queryExact(const std::string &englishWord) const {
    std::vector<WordEntry> results;
    std::string target = toLower(englishWord);
    for (const auto &entry : entriesArray_) {
        if (toLower(entry.english) == target) {
            results.push_back(entry);
        }
    }
    return results;
}

std::vector<WordEntry> Dictionary::queryFuzzy(const std::string &pattern) const {
    std::vector<WordEntry> results;
    std::string target = toLower(pattern);
    for (const auto &entry : entriesArray_) {
        if (toLower(entry.english).find(target) != std::string::npos) {
            results.push_back(entry);
        }
    }
    return results;
}

void Dictionary::displayEntries(const std::vector<WordEntry> &entries) const {
    if (entries.empty()) {
        std::cout << "没有找到匹配的单词。" << std::endl;
        return;
    }
    for (const auto &entry : entries) {
        std::cout << entry.english << " [" << entry.partOfSpeech << "] - " << entry.chinese << std::endl;
    }
}

void Dictionary::exportByInitials(const std::set<char> &initials, const std::string &outputFile) const {
    std::filesystem::create_directories(std::filesystem::path(outputFile).parent_path());
    std::ofstream output(outputFile, std::ios::trunc);
    Node *current = head_;
    while (current != nullptr) {
        char firstChar = current->entry.english.empty() ? '\0'
                         : static_cast<char>(std::tolower(static_cast<unsigned char>(current->entry.english.front())));
        if (initials.count(firstChar) > 0) {
            output << current->entry.english << '\t'
                   << current->entry.partOfSpeech << '\t'
                   << current->entry.chinese << '\n';
        }
        current = current->next;
    }
}
