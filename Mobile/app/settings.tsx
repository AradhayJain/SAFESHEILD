import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, Switch, ScrollView, Modal, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather, MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';

export default function SettingsScreen() {
  const router = useRouter();
  const [isPasswordEnabled, setIsPasswordEnabled] = useState(true);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [transactionLimit, setTransactionLimit] = useState(50000);
  const [showLanguageModal, setShowLanguageModal] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('English');

  const handleLogout = () => {
    router.replace('/login');
  };

  const handleLanguageSelect = (lang: string) => {
    setSelectedLanguage(lang);
    setShowLanguageModal(false);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
        <Feather name="arrow-left" size={24} color="#244A85" />
        <Text style={styles.backText}>Back</Text>
      </TouchableOpacity>
      <MaterialCommunityIcons name="cog-outline" size={60} color="#2CC7A6" style={{ marginBottom: 16, marginTop: 40 }} />
      <Text style={styles.title}>Settings Page</Text>
      <Text style={styles.subtitle}>Manage your account settings and preferences</Text>
      <ScrollView style={{ width: '100%' }} contentContainerStyle={{ alignItems: 'center', paddingBottom: 40 }}>
        {/* Banking Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Banking Settings</Text>
          <View style={styles.row}>
            <Feather name="key" size={20} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Set PIN</Text>
          </View>
          <View style={styles.row}>
            <FontAwesome5 name="lock" size={20} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Change Password</Text>
            <Switch
              value={isPasswordEnabled}
              onValueChange={setIsPasswordEnabled}
              trackColor={{ false: "#ccc", true: "#2CC7A6" }}
              thumbColor={isPasswordEnabled ? "#2CC7A6" : "#f4f3f4"}
              style={{ marginLeft: 'auto' }}
            />
          </View>
          <TouchableOpacity style={styles.row} onPress={() => Alert.alert('Biometric Login', 'This is a dummy action for now.')}>
            <MaterialCommunityIcons name="fingerprint" size={22} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Biometric Login</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.row} onPress={() => Alert.alert('Manage Linked Devices', 'This is a dummy action for now.')}>
            <Feather name="smartphone" size={20} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Manage Linked Devices</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.row} onPress={() => setShowLimitModal(true)}>
            <MaterialCommunityIcons name="cash-multiple" size={22} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Set Transaction Limits</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
        </View>
        {/* Notifications & Security */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications & Security</Text>
          <TouchableOpacity style={styles.row} onPress={() => Alert.alert('Two-Factor Authentication', 'This is a dummy action for now.')}>
            <MaterialCommunityIcons name="shield-check" size={22} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Two-Factor Authentication</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.row} onPress={() => Alert.alert('Manage Notifications', 'This is a dummy action for now.')}>
            <Feather name="bell" size={20} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Manage Notifications</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
        </View>
        {/* App Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Preferences</Text>
          <TouchableOpacity style={styles.row} onPress={() => setShowLanguageModal(true)}>
            <Feather name="globe" size={20} color="#244A85" style={styles.icon} />
            <Text style={styles.optionText}>Language ({selectedLanguage})</Text>
            <Feather name="chevron-right" size={22} color="#244A85" style={{ marginLeft: 'auto' }} />
          </TouchableOpacity>
        </View>
        {/* Logout */}
        <View style={styles.section}>
          <TouchableOpacity style={styles.logoutRow} onPress={handleLogout}>
            <MaterialCommunityIcons name="logout" size={22} color="#FF3B30" style={styles.icon} />
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
      {/* Transaction Limit Modal */}
      <Modal
        visible={showLimitModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLimitModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Set Transaction Limit</Text>
            <Text style={styles.limitValue}>₹{transactionLimit.toLocaleString()}</Text>
            <Slider
              style={{ width: '100%', height: 40 }}
              minimumValue={1000}
              maximumValue={100000}
              step={1000}
              minimumTrackTintColor="#2CC7A6"
              maximumTrackTintColor="#ccc"
              thumbTintColor="#2CC7A6"
              value={transactionLimit}
              onValueChange={setTransactionLimit}
            />
            <Pressable style={styles.closeBtn} onPress={() => setShowLimitModal(false)}>
              <Text style={styles.closeBtnText}>Done</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
      {/* Language Modal */}
      <Modal
        visible={showLanguageModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowLanguageModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Language</Text>
            <Pressable onPress={() => handleLanguageSelect('English')} style={{ marginVertical: 8 }}>
              <Text style={{ fontSize: 18, color: selectedLanguage === 'English' ? '#2CC7A6' : '#244A85' }}>English</Text>
            </Pressable>
            <Pressable onPress={() => handleLanguageSelect('Hindi')} style={{ marginVertical: 8 }}>
              <Text style={{ fontSize: 18, color: selectedLanguage === 'Hindi' ? '#2CC7A6' : '#244A85' }}>Hindi</Text>
            </Pressable>
            <Pressable onPress={() => handleLanguageSelect('Marathi')} style={{ marginVertical: 8 }}>
              <Text style={{ fontSize: 18, color: selectedLanguage === 'Marathi' ? '#2CC7A6' : '#244A85' }}>Marathi</Text>
            </Pressable>
            <Pressable style={styles.closeBtn} onPress={() => setShowLanguageModal(false)}>
              <Text style={styles.closeBtnText}>Done</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', backgroundColor: '#f7fafd' },
  backBtn: { flexDirection: 'row', alignItems: 'center', position: 'absolute', top: 40, left: 16, zIndex: 10 },
  backText: { marginLeft: 4, fontSize: 16, color: '#244A85' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#244A85', marginBottom: 4, marginTop: 8 },
  subtitle: { fontSize: 16, color: '#244A85', opacity: 0.7, marginBottom: 24 },
  section: {
    width: '90%',
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 18,
    marginTop: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#244A85', marginBottom: 14 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 0.5,
    borderBottomColor: '#e6e6e6',
  },
  icon: { marginRight: 14 },
  optionText: { fontSize: 16, color: '#244A85' },
  logoutRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    justifyContent: 'center',
  },
  logoutText: {
    fontSize: 16,
    color: '#FF3B30',
    fontWeight: 'bold',
    marginLeft: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.25)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '85%',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#244A85',
    marginBottom: 16,
  },
  limitValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2CC7A6',
    marginBottom: 12,
  },
  closeBtn: {
    marginTop: 18,
    backgroundColor: '#2CC7A6',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 32,
  },
  closeBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
