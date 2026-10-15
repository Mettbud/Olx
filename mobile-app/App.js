import { StatusBar } from "expo-status-bar";
import { memo, useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Pressable,
  RefreshControl,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { API_URL, API_TOKEN, POLL_INTERVAL_SECONDS } from "./config";

const AdCard = memo(function AdCard({ item }) {
  return (
    <Pressable style={styles.card} onPress={() => Linking.openURL(item.url)}>
      <Text style={styles.title} numberOfLines={2}>
        {item.title}
      </Text>
      <Text style={styles.price}>{item.price}</Text>
      <Text style={styles.location}>{item.location}</Text>
    </Pressable>
  );
});

// Te same id w tej samej kolejności => nic się wizualnie nie zmieniło,
// nie ma sensu podmieniać tablicy i przerysowywać całej listy.
function sameAdIds(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i].id !== b[i].id) return false;
  }
  return true;
}

export default function App() {
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const adsRef = useRef([]);

  const loadAds = useCallback(async () => {
    try {
      setError(null);
      const url = `${API_URL}?token=${encodeURIComponent(API_TOKEN)}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Serwer zwrócił status ${response.status}`);
      }
      const data = await response.json();
      const nextAds = data.ads ?? [];
      if (!sameAdIds(adsRef.current, nextAds)) {
        adsRef.current = nextAds;
        setAds(nextAds);
      }
    } catch (err) {
      setError(err.message ?? "Nieznany błąd połączenia");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAds();
    const interval = setInterval(loadAds, POLL_INTERVAL_SECONDS * 1000);
    return () => clearInterval(interval);
  }, [loadAds]);

  const onRefresh = () => {
    setRefreshing(true);
    loadAds();
  };

  const renderItem = useCallback(({ item }) => <AdCard item={item} />, []);
  const keyExtractor = useCallback((item) => item.id, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      <Text style={styles.header}>Ogłoszenia OLX ({ads.length})</Text>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>Błąd: {error}</Text>
        </View>
      )}

      {loading ? (
        <ActivityIndicator style={{ marginTop: 40 }} size="large" />
      ) : (
        <FlatList
          data={ads}
          keyExtractor={keyExtractor}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          initialNumToRender={12}
          maxToRenderPerBatch={12}
          windowSize={7}
          removeClippedSubviews
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          ListEmptyComponent={
            <Text style={styles.empty}>Brak ogłoszeń do pokazania.</Text>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f5f5f5",
    paddingTop: 10,
  },
  header: {
    fontSize: 20,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 10,
  },
  list: {
    paddingHorizontal: 12,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
  },
  price: {
    fontSize: 15,
    color: "#1a7a1a",
    fontWeight: "600",
    marginBottom: 2,
  },
  location: {
    fontSize: 13,
    color: "#666",
  },
  empty: {
    textAlign: "center",
    marginTop: 40,
    color: "#888",
  },
  errorBox: {
    backgroundColor: "#ffe0e0",
    padding: 10,
    marginHorizontal: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  errorText: {
    color: "#a00",
  },
});
