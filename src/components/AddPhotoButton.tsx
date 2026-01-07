import React from "react";
import { TouchableOpacity, Text, ActivityIndicator } from "react-native";
import { pickImageFromLibrary } from "../lib/pickImage";
import { API_BASE_URL } from "../config";

export default function AddPhotoButton(){
  const [busy,setBusy]=React.useState(false);
  const onPress = async () => {
    if (busy) return;
    setBusy(true);
    try{
      const img = await pickImageFromLibrary(1600);
      if(!img) return;
      const fd = new FormData();
      fd.append("file", { uri: img.uri, name: "photo.jpg", type: "image/jpeg" } as any);
      await fetch(`${API_BASE_URL}/report`, { method: "POST", body: fd });
    } finally { setBusy(false); }
  };
  return (
    <TouchableOpacity onPress={onPress} style={{ padding:12, borderRadius:12, backgroundColor:"#0B2E4A" }}>
      {busy ? <ActivityIndicator/> : <Text style={{ color:"white", fontWeight:"600" }}>Add photo</Text>}
    </TouchableOpacity>
  );
}
