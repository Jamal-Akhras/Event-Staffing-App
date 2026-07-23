import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { COLORS } from "../../theme/colors";
import { FILTERS, type ShiftFilter } from "./browseUtils";

type BrowseFiltersProps = {
  activeFilter: ShiftFilter;
  searchQuery: string;
  onFilterChange: (filter: ShiftFilter) => void;
  onSearchChange: (query: string) => void;
};

export function BrowseFilters({
  activeFilter,
  searchQuery,
  onFilterChange,
  onSearchChange,
}: BrowseFiltersProps) {
  return (
    <View style={styles.container}>
      <TextInput
        style={styles.searchInput}
        placeholder="Search role or location"
        placeholderTextColor={COLORS.inkSubtle}
        value={searchQuery}
        onChangeText={onSearchChange}
      />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filters}
      >
        {FILTERS.map((filter) => {
          const isActive = activeFilter === filter.key;
          return (
            <Pressable
              key={filter.key}
              style={[styles.filterChip, isActive && styles.filterChipActive]}
              onPress={() => onFilterChange(filter.key)}
            >
              <Text style={[styles.filterChipText, isActive && styles.filterChipTextActive]}>
                {filter.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12 },
  searchInput: {
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    color: COLORS.ink,
    fontSize: 15,
  },
  filters: { gap: 10, paddingBottom: 8 },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 999,
    backgroundColor: COLORS.surface,
  },
  filterChipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  filterChipText: { color: COLORS.inkMuted, fontWeight: "800" },
  filterChipTextActive: { color: COLORS.onPrimary },
});
