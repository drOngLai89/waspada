import * as ImagePicker from "expo-image-picker";
import * as ImageManipulator from "expo-image-manipulator";

export type PickResult = { uri:string; fileName:string; mime:string; width:number; height:number };

export async function pickImageFromLibrary(maxSide = 1600): Promise<PickResult | null> {
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (perm.status !== "granted") return null;

  const res = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
    allowsMultipleSelection: false,
    allowsEditing: false,
    quality: 1,
    exif: false,
    base64: false
  });
  if (res.canceled) return null;

  const a = res.assets[0];
  const w = a.width ?? 0, h = a.height ?? 0;
  const scale = Math.min(1, maxSide / Math.max(w || maxSide, h || maxSide));
  const target = (scale < 1 && w && h) ? { width: Math.round(w * scale) } : undefined;

  const out = await ImageManipulator.manipulateAsync(
    a.uri,
    target ? [{ resize: target }] : [],
    { compress: 0.75, format: ImageManipulator.SaveFormat.JPEG }
  );

  return { uri: out.uri, fileName: "photo.jpg", mime: "image/jpeg", width: out.width ?? w, height: out.height ?? h };
}
