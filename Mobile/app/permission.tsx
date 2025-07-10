import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function PermissionScreen() {
  const router = useRouter();

  const handleAccept = () => {
    router.replace('/register');
  };

  const handleDecline = () => {
    router.replace('/welcome');
  };

  return (
    <View style={styles.container}>
      <View style={styles.iconBox}>
        <MaterialCommunityIcons name="shield-lock-outline" size={48} color="#2CC7A6" />
      </View>
      <Text style={styles.title}>Permission Required</Text>
      <Text style={styles.subtitle}>
        SafeShield needs your permission to track behavioral data for secure authentication and fraud prevention.
      </Text>
      <Text style={styles.infoTitle}>We will track the following parameters:</Text>
      <View style={styles.listBox}>
        <Text style={styles.listItem}>• Hold Time</Text>
        <Text style={styles.listItem}>• Flight Time</Text>
        <Text style={styles.listItem}>• Backspace Rate</Text>
        <Text style={styles.listItem}>• Typing Speed</Text>
        <Text style={styles.listItem}>• Swipe Distance</Text>
        <Text style={styles.listItem}>• Swipe Duration</Text>
        <Text style={styles.listItem}>• Swipe Speed</Text>
        <Text style={styles.listItem}>• Swipe Direction</Text>
        <Text style={styles.listItem}>• Swipe Acceleration</Text>
      </View>
      <Text style={styles.whyText}>
        This data is used only for behavioral authentication and fraud detection. Your privacy is our priority.
      </Text>
      <TouchableOpacity style={styles.acceptBtn} onPress={handleAccept}>
        <Text style={styles.acceptBtnText}>Yes, I Allow</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.declineBtn} onPress={handleDecline}>
        <Text style={styles.declineBtnText}>No, I Do Not Allow</Text>
      </TouchableOpacity>
      <Text style={styles.requiredText}>
        {`Permission is required to use SafeShield.\nIf you do not allow, you cannot proceed.`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7fafd', alignItems: 'center', justifyContent: 'center', padding: 24 },
  iconBox: { backgroundColor: '#e5f1ff', borderRadius: 24, padding: 18, marginBottom: 18 },
  title: { fontSize: 26, fontWeight: 'bold', color: '#244A85', marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 15, color: '#244A85', marginBottom: 18, textAlign: 'center' },
  infoTitle: { fontSize: 16, fontWeight: 'bold', color: '#244A85', marginBottom: 8, textAlign: 'center' },
  listBox: { alignSelf: 'stretch', marginBottom: 18, paddingLeft: 24 },
  listItem: { fontSize: 15, color: '#1976D2', marginBottom: 2 },
  whyText: { fontSize: 13, color: '#888', marginBottom: 22, textAlign: 'center' },
  acceptBtn: { backgroundColor: '#2CC7A6', borderRadius: 8, padding: 14, alignItems: 'center', width: '100%', marginBottom: 10 },
  acceptBtnText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  declineBtn: { backgroundColor: '#e5f9f5', borderRadius: 8, padding: 14, alignItems: 'center', width: '100%' },
  declineBtnText: { color: '#244A85', fontSize: 16, fontWeight: '500' },
  requiredText: { color: '#E53935', fontSize: 14, marginTop: 18, textAlign: 'center' },
});