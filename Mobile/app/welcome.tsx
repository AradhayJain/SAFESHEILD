import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <View style={styles.center}>
        <View style={styles.iconBox}>
          <MaterialCommunityIcons name="shield-outline" size={56} color="#2CC7A6" />
        </View>
        <Text style={styles.title}>SafeShield</Text>
        <Text style={styles.subtitle}>Invisible Protection</Text>
        <View style={styles.featureBox}>
          <View style={styles.featureRow}>
            <MaterialCommunityIcons name="brain" size={20} color="#fff" />
            <Text style={styles.featureText}>Behavioral Intelligence</Text>
          </View>
          <View style={styles.featureRow}>
            <MaterialCommunityIcons name="flash" size={20} color="#fff" />
            <Text style={styles.featureText}>Zero Friction Authentication</Text>
          </View>
          <View style={styles.featureRow}>
            <MaterialCommunityIcons name="lock-outline" size={20} color="#fff" />
            <Text style={styles.featureText}>Privacy-First Security</Text>
          </View>
        </View>
      </View>
      <TouchableOpacity 
        style={styles.button} 
        onPress={() => router.push('/login')} // Fixed: Use push for navigation
      >
        <Text style={styles.buttonText}>Get Started</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#244A85', justifyContent: 'center' },
  center: { alignItems: 'center', marginTop: 60 },
  iconBox: { backgroundColor: '#fff', borderRadius: 16, padding: 24, marginBottom: 24 },
  title: { fontSize: 32, color: '#fff', fontWeight: 'bold', marginBottom: 8 },
  subtitle: { fontSize: 18, color: '#fff', marginBottom: 24 },
  featureBox: { marginTop: 8 },
  featureRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  featureText: { color: '#fff', fontSize: 16, marginLeft: 8 },
  button: { backgroundColor: '#2CC7A6', margin: 32, borderRadius: 8, padding: 16, alignItems: 'center' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
});
