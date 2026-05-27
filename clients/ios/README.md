# clients/ios — Jarvis iOS (SwiftUI)

> ⚠️ İskelet. Xcode gerektirir; bu repoda derlenmez/doğrulanmaz.

SwiftUI ile minimal Jarvis istemcisi. Mac sunucusuna Tailscale üzerinden bağlanır.

## Dosyalar
- `JarvisApp.swift` — uygulama girişi
- `JarvisClient.swift` — async API istemcisi (cihaz anahtarı → JWT, /chat)
- `ContentView.swift` — sohbet arayüzü + view model

## Kurulum
1. Xcode'da yeni bir **iOS App** projesi oluşturun (SwiftUI).
2. Bu üç `.swift` dosyasını projeye ekleyin (şablon dosyalarını değiştirin).
3. `ContentView.swift` içindeki `baseURL` ve `deviceKey`'i kendi
   Tailscale adresinize/cihaz anahtarınıza göre düzenleyin.
4. iPhone'unuzda Tailscale kurulu ve aynı tailnet'te olsun.
5. Çalıştırın.

> HTTP (TLS yok) kullanıyorsanız `Info.plist`'e App Transport Security
> istisnası eklemeniz gerekebilir (Tailscale IP/host için), ya da API'yi
> TLS arkasına alın.

## Shortcuts entegrasyonu (öneri)
"Hey Siri, Jarvis'e sor" akışı için:
1. Kısayollar uygulamasında **"URL'nin İçeriğini Al"** eylemi ekleyin.
2. `POST {baseURL}/auth/token` ile token alın (cihaz anahtarı gövdede).
3. `POST {baseURL}/chat` çağrısını `Authorization: Bearer <token>` ile yapın.
4. Dönen `content` alanını **"Metni Söyle"** ile okutun.
5. Kısayola Siri ifadesi atayın: "Jarvis'e sor".
