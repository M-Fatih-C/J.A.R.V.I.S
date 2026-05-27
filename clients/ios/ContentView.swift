// ContentView.swift — basit sohbet arayüzü.

import SwiftUI

struct Message: Identifiable {
    let id = UUID()
    let role: String  // "Siz" | "Jarvis"
    let text: String
}

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var draft: String = ""
    @Published var busy = false

    // Tailscale adresinizi ve cihaz anahtarınızı buraya girin.
    private let client = JarvisClient(
        baseURL: URL(string: "http://mac.tail-scale.ts.net:8000")!,
        deviceKey: "change-me-device-key"
    )

    func send() {
        let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !busy else { return }
        messages.append(Message(role: "Siz", text: text))
        draft = ""
        busy = true
        Task {
            do {
                let result = try await client.chat(text)
                messages.append(Message(role: "Jarvis", text: result.content))
            } catch {
                messages.append(Message(role: "Hata", text: "\(error)"))
            }
            busy = false
        }
    }
}

struct ContentView: View {
    @StateObject private var model = ChatViewModel()

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(model.messages) { msg in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(msg.role).font(.caption).foregroundStyle(.secondary)
                            Text(msg.text)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding()
            }
            HStack {
                TextField("Bir şey sorun, efendim…", text: $model.draft)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { model.send() }
                Button("Gönder") { model.send() }
                    .disabled(model.busy)
            }
            .padding()
        }
        .navigationTitle("J.A.R.V.I.S")
    }
}
