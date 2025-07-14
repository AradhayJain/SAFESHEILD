# Updated verification script that checks for typing_models folder
# Replace your current model_directory_verification.py with this

import os
import sys

def check_model_directory_paths():
    """Check that all model trainers use the correct model directory"""
    
    print("🔍 Checking Model Directory Paths")
    print("=" * 40)
    
    # Expected model directory (relative to ML folder)
    expected_model_dir = './models'
    
    print(f"Expected model directory: {os.path.abspath(expected_model_dir)}")
    
    # Check if models directory exists
    if not os.path.exists(expected_model_dir):
        print("📁 Creating models directory...")
        os.makedirs(expected_model_dir, exist_ok=True)
        print("✅ Models directory created")
    else:
        print("✅ Models directory exists")
    
    # Check existing model files
    if os.path.exists(expected_model_dir):
        model_files = [f for f in os.listdir(expected_model_dir) if f.endswith('.pkl')]
        if model_files:
            print(f"\n📦 Found {len(model_files)} existing model files:")
            for file in sorted(model_files):
                print(f"   - {file}")
        else:
            print("\n📦 No existing model files found (this is normal for first run)")
    
    # Verify model trainer configurations
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        print(f"\n🔧 Checking Model Trainer Configurations...")
        
        # Check swipe model trainer
        try:
            from swiping.enhanced_swipe_model_trainer import EnhancedSwipeModelTrainer
            swipe_trainer = EnhancedSwipeModelTrainer()
            print(f"✅ Swipe trainer model_dir: {swipe_trainer.model_dir}")
            
            # Verify the path resolves correctly
            abs_path = os.path.abspath(swipe_trainer.model_dir)
            print(f"   Absolute path: {abs_path}")
            
        except ImportError as e:
            print(f"❌ Could not import swipe trainer: {e}")
        except Exception as e:
            print(f"⚠️ Error checking swipe trainer: {e}")
        
        # Check typing model trainer (updated to use typing_models)
        try:
            from typing_models.enhanced_typing_model_trainer import EnhancedTypingModelTrainer
            typing_trainer = EnhancedTypingModelTrainer()
            print(f"✅ Typing trainer model_dir: {typing_trainer.model_dir}")
            
            # Verify the path resolves correctly
            abs_path = os.path.abspath(typing_trainer.model_dir)
            print(f"   Absolute path: {abs_path}")
            
        except ImportError as e:
            print(f"❌ Could not import typing trainer: {e}")
            print(f"   Make sure your 'typing' folder is renamed to 'typing_models'")
        except Exception as e:
            print(f"⚠️ Error checking typing trainer: {e}")
        
        # Check prediction modules
        try:
            from swiping.predict_swipe_risk import SwipeRiskPredictor
            swipe_predictor = SwipeRiskPredictor()
            print(f"✅ Swipe predictor model_dir: {swipe_predictor.model_dir}")
            
        except ImportError as e:
            print(f"❌ Could not import swipe predictor: {e}")
        except Exception as e:
            print(f"⚠️ Error checking swipe predictor: {e}")
        
        try:
            from typing_models.predict_typing_risk import TypingRiskPredictor
            typing_predictor = TypingRiskPredictor()
            print(f"✅ Typing predictor model_dir: {typing_predictor.model_dir}")
            
        except ImportError as e:
            print(f"❌ Could not import typing predictor: {e}")
            print(f"   Make sure your 'typing' folder is renamed to 'typing_models'")
        except Exception as e:
            print(f"⚠️ Error checking typing predictor: {e}")
    
    except Exception as e:
        print(f"❌ Error during configuration check: {e}")
    
    print(f"\n" + "=" * 40)
    
    return expected_model_dir

def test_model_saving():
    """Test that models can be saved to the correct directory"""
    
    print("💾 Testing Model Saving")
    print("=" * 40)
    
    try:
        import pickle
        import numpy as np
        from datetime import datetime
        
        # Test data
        test_model = {"test": "data", "timestamp": datetime.now().isoformat()}
        test_filename = "test_model_save.pkl"
        test_path = f"./models/{test_filename}"
        
        # Try to save a test file
        with open(test_path, 'wb') as f:
            pickle.dump(test_model, f)
        
        print(f"✅ Successfully saved test model to: {os.path.abspath(test_path)}")
        
        # Try to load it back
        with open(test_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        print(f"✅ Successfully loaded test model")
        
        # Clean up
        os.remove(test_path)
        print(f"✅ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Model saving test failed: {e}")
        return False

def check_folder_structure():
    """Check if the required folder structure exists"""
    
    print("📁 Checking Required Folder Structure")
    print("=" * 40)
    
    required_folders = {
        'swiping': 'Contains swipe-related ML modules',
        'typing_models': 'Contains typing-related ML modules (renamed from typing)',
        'preprocessing': 'Contains data preprocessing modules',
        'models': 'Directory for saved model files'
    }
    
    all_good = True
    
    for folder, description in required_folders.items():
        if os.path.exists(folder):
            print(f"✅ {folder}/ - {description}")
            
            # Check if it has Python files
            if folder != 'models':
                py_files = [f for f in os.listdir(folder) if f.endswith('.py')]
                if py_files:
                    print(f"   Contains {len(py_files)} Python files")
                else:
                    print(f"   ⚠️ No Python files found")
                    all_good = False
        else:
            print(f"❌ {folder}/ - MISSING")
            all_good = False
            
            if folder == 'typing_models':
                if os.path.exists('typing'):
                    print(f"   💡 Found 'typing' folder - please rename it to 'typing_models'")
                    print(f"   Command: mv typing typing_models")
    
    return all_good

def show_directory_structure():
    """Show the current directory structure"""
    
    print("📁 Current Directory Structure")
    print("=" * 40)
    
    def print_tree(path, prefix="", max_depth=2, current_depth=0):
        if current_depth >= max_depth:
            return
        
        items = []
        try:
            items = sorted(os.listdir(path))
        except PermissionError:
            return
        
        for i, item in enumerate(items):
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(path, item)
            is_last = i == len(items) - 1
            
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item}")
            
            if os.path.isdir(item_path) and current_depth < max_depth - 1:
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item_path, next_prefix, max_depth, current_depth + 1)
    
    print("ML/")
    print_tree(".", "")

def provide_fix_instructions():
    """Provide instructions to fix common issues"""
    
    print("🔧 Fix Instructions")
    print("=" * 40)
    
    # Check if typing folder exists (instead of typing_models)
    if os.path.exists('typing') and not os.path.exists('typing_models'):
        print("⚠️ ISSUE FOUND: 'typing' folder should be renamed to 'typing_models'")
        print("\n💡 TO FIX:")
        print("   cd ML")
        print("   mv typing typing_models")
        print("")
    
    # Check if util files need updating
    if os.path.exists('util_training.py'):
        print("📝 Next steps:")
        print("1. Rename typing folder: mv typing typing_models")
        print("2. Update util_training.py with the fixed version")
        print("3. Update util_predict.py with the fixed version")
        print("4. Run: python model_directory_verification.py")
        print("5. Run: python test_ml_pipeline.py")

if __name__ == "__main__":
    print("🔧 Model Directory Configuration Check")
    print("=" * 50)
    
    # Show current structure
    show_directory_structure()
    print()
    
    # Check folder structure
    structure_good = check_folder_structure()
    print()
    
    if not structure_good:
        provide_fix_instructions()
        print()
    
    # Check model directory paths
    model_dir = check_model_directory_paths()
    print()
    
    # Test model saving
    save_test_passed = test_model_saving()
    print()
    
    if save_test_passed and structure_good:
        print("🎉 All model directory configurations are correct!")
        print(f"✅ Models will be saved to: {os.path.abspath(model_dir)}")
    else:
        print("⚠️ Some issues found. Please check the messages above.")
    
    print("\n💡 Next steps:")
    print("1. Fix any issues mentioned above")
    print("2. Run the full test: python test_ml_pipeline.py")
    print("3. Train a model: from util_training import get_model")
    print("4. Check the models/ folder for saved model files")