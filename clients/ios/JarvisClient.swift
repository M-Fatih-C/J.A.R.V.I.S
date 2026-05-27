// JarvisClient.swift — Jarvis API'sine bağlanan async istemci.
//
// Cihaz anahtarıyla token alır ve korunan uç noktalara Bearer ile erişir.

import Foundation

struct TokenResponse: Codable {
    let access_token: String
    let token_type: String
}

struct ChatResult: Codable {
    let content: String
    let lane: String?
    let model: String?
    let latency_ms: Double?
}

enum JarvisError: Error {
    case missingDeviceKey
    case http(Int)
}

/// Jarvis API'sine erişen hafif async istemci.
actor JarvisClient {
    private let baseURL: URL
    private let deviceKey: String?
    private var token: String?

    init(baseURL: URL, deviceKey: String? = nil, token: String? = nil) {
        self.baseURL = baseURL
        self.deviceKey = deviceKey
        self.token = token
    }

    /// Cihaz anahtarıyla bir erişim token'ı alır ve saklar.
    @discardableResult
    func authenticate() async throws -> String {
        guard let deviceKey else { throw JarvisError.missingDeviceKey }
        var request = URLRequest(url: baseURL.appendingPathComponent("auth/token"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["device_key": deviceKey])

        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.check(response)
        let decoded = try JSONDecoder().decode(TokenResponse.self, from: data)
        token = decoded.access_token
        return decoded.access_token
    }

    /// Bir sohbet mesajı gönderir; token yoksa otomatik kimlik doğrular.
    func chat(_ message: String, sessionId: String = "ios") async throws -> ChatResult {
        if token == nil, deviceKey != nil {
            try await authenticate()
        }
        var request = URLRequest(url: baseURL.appendingPathComponent("chat"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = try JSONEncoder().encode(
            ["message": message, "session_id": sessionId]
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        try Self.check(response)
        return try JSONDecoder().decode(ChatResult.self, from: data)
    }

    private static func check(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200..<300).contains(http.statusCode) else {
            throw JarvisError.http(http.statusCode)
        }
    }
}
