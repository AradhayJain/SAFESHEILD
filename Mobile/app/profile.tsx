import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Platform, StatusBar, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons, Feather } from '@expo/vector-icons';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const scale = (size: number) => (SCREEN_WIDTH / 375) * size; // 375 is iPhone 11 width

export default function ProfileScreen() {
  const router = useRouter();

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ScrollView style={styles.container}>
        <View style={styles.headerBox}>
          <TouchableOpacity 
            style={styles.backBtn} 
            onPress={() => router.back()}
          >
            <Feather name="arrow-left" size={24} color="#244A85" />
          </TouchableOpacity>
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
          </View>
          <View style={styles.confidenceRow}>
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
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f7fafd', 
    padding: 0, 
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : scale(8), // Add top padding for status bar
  },
  headerBox: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingVertical: scale(16), // Reduce vertical padding
    paddingHorizontal: scale(20), 
    backgroundColor: '#fff', 
    borderBottomWidth: 1, 
    borderColor: '#f0f0f0' 
  },
  backBtn: { 
    marginRight: scale(12), 
  },
  headerTitle: { fontWeight: 'bold', fontSize: scale(20), color: '#244A85' },
  profileCard: {
    backgroundColor: '#fff',
    borderRadius: scale(18),
    alignItems: 'center',
    padding: scale(24),
    margin: scale(16),
    marginBottom: scale(18),
    elevation: 2,
  },
  avatarBox: {
    backgroundColor: '#e5f1ff',
    borderRadius: scale(50),
    width: scale(70),
    height: scale(70),
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: scale(10),
  },
  name: { fontWeight: 'bold', fontSize: scale(22), color: '#244A85', marginTop: scale(6) },
  accountType: { color: '#b0b0b0', marginBottom: scale(18), marginTop: scale(2) },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    marginTop: 0,
    marginBottom: scale(6),
    gap: scale(8),
  },
  confidenceRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    marginTop: 0,
    marginBottom: 0,
    gap: scale(8),
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f8ee',
    borderRadius: scale(8),
    paddingVertical: scale(6),
    paddingHorizontal: scale(10),
    marginRight: 0,
    flex: 1,
    justifyContent: 'center',
    minWidth: 0,
  },
  statusText: { color: '#244A85', marginLeft: scale(4), fontSize: scale(13) },
  statusActive: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: scale(6), fontSize: scale(13) },
  confidenceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f2fd',
    borderRadius: scale(8),
    paddingVertical: scale(6),
    paddingHorizontal: scale(10),
    marginLeft: 0,
    flex: 1,
    justifyContent: 'center',
    minWidth: 0,
  },
  confidenceText: { color: '#244A85', marginLeft: scale(4), fontSize: scale(13) },
  confidenceValue: { color: '#2CC7A6', fontWeight: 'bold', marginLeft: scale(6), fontSize: scale(13) },
  sectionTitle: { fontSize: scale(18), fontWeight: 'bold', color: '#244A85', marginBottom: scale(8), marginLeft: scale(16) },
  infoBox: { backgroundColor: '#fff', borderRadius: scale(10), padding: scale(16), marginHorizontal: scale(16), marginBottom: scale(12), elevation: 1 },
  infoHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: scale(4) },
  infoTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: scale(6), fontSize: scale(15) },
  infoStatus: { color: '#a259ff', fontWeight: 'bold', fontSize: scale(13), marginLeft: scale(10) },
  infoStatusOpt: { color: '#2CC7A6', fontWeight: 'bold', fontSize: scale(13), marginLeft: scale(10) },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: scale(2), marginTop: scale(6) },
  infoValue: { fontWeight: 'bold', fontSize: scale(16) },
  infoLabel: { color: '#b0b0b0', fontSize: scale(13) },
  contextBox: { backgroundColor: '#fff', borderRadius: scale(10), padding: scale(16), marginHorizontal: scale(16), marginBottom: scale(24), elevation: 1 },
  contextHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: scale(4) },
  contextTitle: { fontWeight: 'bold', color: '#244A85', marginLeft: scale(6), fontSize: scale(15) },
  contextStatus: { color: '#2CC7A6', fontWeight: 'bold', fontSize: scale(13), marginLeft: scale(10) },
  contextRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: scale(2) },
  contextLabel: { color: '#244A85', fontWeight: 'bold', fontSize: scale(15) },
  contextSubLabel: { color: '#b0b0b0', fontSize: scale(13) },
});
