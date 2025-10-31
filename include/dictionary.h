#ifndef DICTIONARY_H
#define DICTIONARY_H

#include <string>
#include <vector>
#include <set>

struct WordEntry {
    std::string english;
    std::string partOfSpeech;
    std::string chinese;
};

class Dictionary {
public:
    explicit Dictionary(const std::string &dictionaryFilePath);
    ~Dictionary();

    void loadFromFile();
    void saveToFile() const;

    void inputEntries(std::size_t count);
    void displayAll() const;
    void insertEntry(const WordEntry &entry);
    bool deleteEntry(const std::string &englishWord);
    bool modifyEntry(const std::string &englishWord, const WordEntry &updatedEntry);

    std::vector<WordEntry> queryExact(const std::string &englishWord) const;
    std::vector<WordEntry> queryFuzzy(const std::string &pattern) const;
    void displayEntries(const std::vector<WordEntry> &entries) const;

    void exportByInitials(const std::set<char> &initials, const std::string &outputFile) const;

private:
    struct Node {
        WordEntry entry;
        Node *next = nullptr;
    };

    void clearList();
    void rebuildListFromArray();
    void insertIntoListSorted(const WordEntry &entry);

    std::vector<WordEntry> entriesArray_;
    Node *head_ = nullptr;
    std::string dictionaryFilePath_;
};

#endif // DICTIONARY_H
