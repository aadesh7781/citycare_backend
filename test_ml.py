from utils.ml_model import predict_score
print(predict_score("There is a large pothole on the main road causing accidents"))
print(predict_score("Sewage water overflowing "))
print(predict_score("Broken streetlight"))

print(predict_score("pothole"))