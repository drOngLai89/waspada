import * as ImagePicker from "expo-image-picker";
import * as ImageManipulator from "expo-image-manipulator";

function getImagesMediaType() {
  const anyPicker: any = ImagePicker as any;
  return anyPicker?.MediaType?.Images ?? anyPicker?.MediaTypeOptions?.Images;
}

export async function pickScreenshotDataUrl(): Promise<{ dataUrl: string; approxBytes: number } | null> {
  const mediaTypes = getImagesMediaType();

  const res = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: mediaTypes ? mediaTypes : undefined,
    quality: 0.85,
    base64: true,
    allowsEditing: false,
  });

  if ((res as any).canceled) return null;

  const asset = (res as any).assets?.[0];
  if (!asset?.uri) return null;

  // Resize/compress to keep payload smaller and more reliable
  const manipulated = await ImageManipulator.manipulateAsync(
    asset.uri,
    [{ resize: { width: 1100 } }],
    { compress: 0.72, format: ImageManipulator.SaveFormat.JPEG, base64: true }
  );

  const b64 = manipulated.base64;
  if (!b64) return null;

  const dataUrl = `data:image/jpeg;base64,${b64}`;
  const approxBytes = Math.floor((b64.length * 3) / 4);

  return { dataUrl, approxBytes };
}
