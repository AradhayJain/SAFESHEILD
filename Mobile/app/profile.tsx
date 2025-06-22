import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';

export default function ProfileScreen() {
  const router = useRouter();

  return (
    <ScrollView style={styles.container}>
      {/* Back button */}
      <TouchableOpacity 
        style={styles.backBtn} 
        onPress={() => router.back()}
      >
        <Feather name="arrow-left" size={24} color="#244A85" />
      </TouchableOpacity>
      
      <View style={styles.headerBox}>
        <Text style={styles.headerTitle}>SafeShield Profile</Text>
      </View>

      <View style={styles.profileCard}>
        <View style={styles.avatarBox}>
          <MaterialCommunityIcons name="account-circle-outline" size={60} color="#2CC7A6" />
        </View>
        <Text style={styles.name}>John Doe</Text>
        <Text style={styles.accountType}>Premium Account</Text>
        <View style={styles.statusRow}>
          <View style={styles.statusBadge}>
            <MaterialCommunityIcons name="shield-outline" size={18} color="#2CC7A6" />
            <Text style={styles.statusText}>SafeShield Status</Text>
            <Text style={styles.statusActive}>Active</Text>
          </View>
          <View style={styles.confidenceBadge}>
            <MaterialCommunityIcons name="brain" size={18} color="#2CC7A6" />
            <Text style={styles.confidenceText}>Behavior Confidence</Text>
            <Text style={styles.confidenceValue}>16.0%</Text>
          </View>
        </View>
      </View>

      <Text style={styles.sectionTitle}>Behavioral Intelligence</Text>
      <View style={styles.infoBox}>
        <View style={styles.infoHeader}>
          <MaterialCommunityIcons name="gesture-tap" size={20} color="#a259ff" />
          <Text style={styles.infoTitle}>Touch Dynamics</Text>
          <Text style={styles.infoStatus}>Learning</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={[styles.infoValue, { color: '#a259ff' }]}>2.3s</Text>
          <Text style={[styles.infoValue, { color: '#a259ff' }]}>145ms</Text>
          <Text style={[styles.infoValue, { color: '#a259ff' }]}>78%</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Avg Touch</Text>
          <Text style={styles.infoLabel}>Pressure</Text>
          <Text style={styles.infoLabel}>Accuracy</Text>
        </View>
      </View>
      <View style={styles.infoBox}>
        <View style={styles.infoHeader}>
          <MaterialCommunityIcons name="gesture-swipe" size={20} color="#2CC7A6" />
          <Text style={styles.infoTitle}>Navigation Patterns</Text>
          <Text style={styles.infoStatusOpt}>Optimized</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={[styles.infoValue, { color: '#ff9900' }]}>1.2s</Text>
          <Text style={[styles.infoValue, { color: '#ff9900' }]}>89%</Text>
          <Text style={[styles.infoValue, { color: '#ff9900' }]}>94%</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Swipe Speed</Text>
          <Text style={styles.infoLabel}>Flow Match</Text>
          <Text style={styles.infoLabel}>Confidence</Text>
        </View>
      </View>
      <View style={styles.contextBox}>
        <View style={styles.contextHeader}>
          <MaterialCommunityIcons name="map-marker-radius-outline" size={20} color="#2CC7A6" />
          <Text style={styles.contextTitle}>Context Awareness</Text>
          <Text style={styles.contextStatus}>Secure</Text>
        </View>
        <View style={styles.contextRow}>
          <Text style={styles.contextLabel}>Home</Text>
          <Text style={[styles.contextLabel, { color: '#2CC7A6' }]}>iPhone 15</Text>
        </View>
        <View style={styles.contextRow}>
          <Text style={styles.contextSubLabel}>Current Location</Text>
          <Text style={styles.contextSubLabel}>Trusted Device</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f7fafd', padding: 0 },
  backBtn: { margin: 16 },
  headerBox: { flexDirection: 'row', alignItems: 'center', padding: 20, backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#f0f0f0' },
  headerTitle: { fontWeight: 'bold', fontSize: 20, color: '#244A85' },
  profileCard: { backgroundColor: '#fff', borderRadius: 18, alignItems: 'center', padding: 24, margin: 16, marginBottom: 18, elevation: 2 },
  avatarBox: { backgroundColor: '#e5f1ff', borderRadius: 50, width: 70, height: 70, alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  name: { fontWeight: 'bold', fontSize: 22, color: '#244A85' },
  accountType: { color: '#b0b0b0', marginBottom: 10 },
  statusRow: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', marginTop: 10 },
  statusBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#e8f8ee', borderRadius: 8, padding: 6, flex: 1, marginRight: 4 },
  statusText: { color: '#244A85', marginLeft: 4, fontSize: 13 },
  statusActive: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: 6, fontSize: 13 },
  confidenceBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#e8f2fd', borderRadius: 8, padding: 6, flex: 1, marginLeft: 4 },
  confidenceText: { color: '#244A85', marginLeft: 4, fontSize: 13 },
  confidenceValue: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: 6, fontSize: 13 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#244A85', marginBottom: 8, marginLeft: 16 },
  infoBox: { backgroundColor: '#fff', borderRadius: 10, padding: 16, marginHorizontal: 16, marginBottom: 12, elevation: 1 },
  infoHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  infoTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: 6, fontSize: 15 },
  infoStatus: { color: '#a259ff', fontWeight: 'bold', fontSize: 13, marginLeft: 10 },
  infoStatusOpt: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 13, marginLeft: 10 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2, marginTop: 6 },
  infoValue: { fontWeight: 'bold', fontSize: 16 },
  infoLabel: { color: '#b0b0b0', fontSize: 13 },
  contextBox: { backgroundColor: '#fff', borderRadius: 10, padding: 16, marginHorizontal: 16, marginBottom: 24, elevation: 1 },
  contextHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  contextTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: 6, fontSize: 15 },
  contextStatus: { color: '#2CC7A6', fontWeight: 'bold', fontSize: 13, marginLeft: 10 },
  contextRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 },
  contextLabel: { color: '#244A85', fontWeight: 'bold', fontSize: 15 },
  contextSubLabel: { color: '#b0b0b0', fontSize: 13 },
});
