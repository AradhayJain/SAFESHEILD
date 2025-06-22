import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';

export default function SettingsScreen() {
  const router = useRouter();

  const handleLogout = () => {
    // You can add any logout logic here if needed
    router.replace('/login'); // Navigate to login page
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
        <Feather name="arrow-left" size={24} color="#244A85" />
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>
      <MaterialCommunityIcons name="cog-outline" size={60} color="#2CC7A6" style={{ marginBottom: 16 }} />
      <Text style={styles.text}>Settings Page</Text>
      <Text style={styles.subtext}>Adjust your preferences here.</Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Banking Settings</Text>
        <TouchableOpacity style={styles.optionBtn} onPress={() => Alert.alert('Set Pin', 'This is a dummy action for now.')}>
          <Feather name="key" size={20} color="#244A85" style={{ marginRight: 10 }} />
          <Text style={styles.optionText}>Set Pin</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.optionBtn} onPress={handleLogout}>
          <Feather name="log-out" size={20} color="#e74c3c" style={{ marginRight: 10 }} />
          <Text style={[styles.optionText, { color: '#e74c3c' }]}>Logout</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f7fafd' },
  backBtn: { flexDirection: 'row', alignItems: 'center', position: 'absolute', top: 40, left: 16 },
  backText: { marginLeft: 4, fontSize: 16, color: '#244A85' },
  text: { fontSize: 24, fontWeight: 'bold', color: '#244A85', marginBottom: 8 },
  subtext: { fontSize: 16, color: '#244A85', opacity: 0.7 },
  section: { width: '85%', marginTop: 40, backgroundColor: '#fff', borderRadius: 10, padding: 20, elevation: 2 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#244A85', marginBottom: 18 },
  optionBtn: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12 },
  optionText: { fontSize: 16, color: '#244A85' },
});
