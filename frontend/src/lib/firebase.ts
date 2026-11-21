import { initializeApp } from "firebase/app";
import {
  getAuth,
  connectAuthEmulator,
  GoogleAuthProvider,
} from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

const firebaseConfig = {
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
};

export const firebaseApp = initializeApp(firebaseConfig);
export const firebaseAuth = getAuth(firebaseApp);
export const firebaseDb = getFirestore(firebaseApp);
// One app, one session — sign-in reuses the instance above rather than standing
// up a second identity stack.
export const googleProvider = new GoogleAuthProvider();

if (import.meta.env.VITE_FIREBASE_USE_EMULATORS === "true") {
  connectAuthEmulator(firebaseAuth, "http://localhost:9099", {
    disableWarnings: true,
  });
  connectFirestoreEmulator(firebaseDb, "localhost", 8085);
}
