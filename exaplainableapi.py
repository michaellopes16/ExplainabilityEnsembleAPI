# -*- coding: utf-8 -*-
"""ExaplainableAPI.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CesI23LUw_ZXlSSqIDGpD_jYIgsk8xko

# **Install Libs**
"""

"""# **IMPORTS**"""

# prompt: crie um classe em python chamada ExplainableAPI com o método load_data que recebe o caminho, o separador e retorna um x e um y
import pandas as pd
import numpy as np

import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.models import load_model
# from multipledispatch import dispatch
import matplotlib.pyplot as plt

import lime.lime_tabular # !pip install lime==0.1.1.37
import shap #!pip install shap==0.46.0

"""# **GENERAL API**"""

class ExplainableAPI:
  QUERY_FUNGI = '''SELECT
            f.name AS Fungi_Name,
            v.VOC_Category,
            COUNT(*) AS VOC_Count
        FROM
            FUNGI f
        JOIN
            FUNGI_VOC fv ON f.id = fv.FUNGI_ID
        JOIN
            VOCs v ON fv.VOC_ID = v.id_VOC
        GROUP BY
            f.name, v.VOC_Category
        ORDER BY
            f.name, v.VOC_Category,VOC_Count;
        '''
  QUERY_SENSOR = '''SELECT
            f.name AS Sensor_Name,
            v.VOC_Category,
            COUNT(*) AS VOC_Count
        FROM
            SENSOR f
        JOIN
            SENSOR_VOC fv ON f.id = fv.SENSOR_ID
        JOIN
            VOCs v ON fv.VOC_ID = v.id_VOC
        GROUP BY
            f.name, v.VOC_Category
        ORDER BY
            f.name,VOC_Count, v.VOC_Category;
        '''
  def __init__(self, features_name):
    self.features_name = features_name
  def load_data(self, path, sep):
      data = pd.read_csv(path, delimiter=sep,header=None)
      print()
      y = data.iloc[:, data.shape[1]-1].values
      x = data.iloc[:,0: data.shape[1]-1].copy().values
      return x, y

  def create_df_2(self, list_weights):
      df = pd.DataFrame({
      'Feature': range(len(list_weights)),
      'Weight': list_weights
      })
      return df

  def get_predicted_class(self, sample, model):
      instancia = np.expand_dims(sample, axis=0)
      result = model.predict(instancia)
      return np.argmax(result[0]) + 1

  def create_df(self, list_weights, features):
      df = pd.DataFrame({
      'Feature': features,
      'Weight': list_weights
      })
      return df
      #melhorar isso
  def get_samples_from_db(self, X_train, y_train, predictedClass):
      # Filtrar as instâncias pela classe desejadacd
      indices_classe = np.where(y_train == predictedClass)[0]
      X_classe = X_train[indices_classe]

      # Selecionar 3 exemplos aleatórios das instâncias filtradas
      amostras_aleatorias = X_classe[np.random.choice(X_classe.shape[0], 3, replace=False)]
      # Converter cada exemplo selecionado em um DataFrame e armazenar em um array
      dataframes = [pd.DataFrame(amostra.reshape(1, -1)) for amostra in amostras_aleatorias]
      return dataframes

  def plot_cycles(self,newDF):
    # Plotando os dataframes em gráficos separados
    for i, df in enumerate(newDF):
        fig = plt.figure(figsize=[20,10])
        plt.plot(df.T, label=f'Ciclo {i+1}')
        plt.title(f'Gráfico de Linha do Ciclo {i+1}')
        plt.xlabel('Índice')
        plt.ylabel('Valores')
        plt.legend()
        plt.show()

    # Mostrando o gráfico
    plt.show()

  def weight_by_feature(self, features_name, weight_list):
      # Converte a lista de pesos em um array NumPy para facilitar a manipulação
      weight_array = np.array(weight_list)

      # Calcula o número de linhas que o DataFrame terá
      num_rows = len(weight_list) // len(features_name)

      # Redimensiona o array para ter 'num_rows' linhas e 'len(features_name)' colunas
      reshaped_array = weight_array[:num_rows * len(features_name)].reshape(num_rows, len(features_name))

      # Cria o DataFrame a partir do array redimensionado
      df = pd.DataFrame(reshaped_array, columns=features_name)
      return df

  def get_final_result(self, wigths, feature):
      df = self.create_df(wigths, feature)
      self.ploat_heatmap(df)
      self.ploat_bar(df)
      df1 = self.weight_by_feature(self.features_name, df.Weight)
      df1.max().plot(kind='bar')
      df1.mean().plot(kind='bar')
      return df1

  def get_most_important_features(self, dataFrame, top_feature_number):

      df = self.weight_by_feature(self.features_name, dataFrame.Weight)

      newDf = df.mean().reset_index()
      newDf.columns = ['Column', 'Mean']
      newDf = newDf.sort_values(by='Mean', ascending=False)
      top_features = newDf.head(top_feature_number)
      return top_features

  def concat_all_mothods(self, means_lime, means_shap, means_grad):
      from sklearn.preprocessing import StandardScaler
      scaler = StandardScaler()
      # Calculando as médias das colunas
      means_lime['Mean'] = scaler.fit_transform(means_lime[['Mean']])
      means_shap['Mean'] = scaler.fit_transform(means_shap[['Mean']])
      means_grad['Mean'] = scaler.fit_transform(means_grad[['Mean']])

      # Renomeando as colunas para facilitar a concatenação
      # Adicionando uma coluna para identificar o dataframe
      means_lime['DataFrame'] = 'LIME'
      means_shap['DataFrame'] = 'SHAP'
      means_grad['DataFrame'] = 'GRAD'

      # Concatenando os dataframes
      means_all = pd.concat([means_lime, means_shap, means_grad])
      return means_all, means_lime, means_shap, means_grad

  def get_top_features(self,means_lime,means_shap,means_grad,top_index ):
      df_sorted_1 = means_lime.sort_values(by='Mean', ascending=False)
      df_sorted_2 = means_shap.sort_values(by='Mean', ascending=False)
      df_sorted_3 = means_grad.sort_values(by='Mean', ascending=False)

      # Selecionar as três primeiras linhas
      top_3_1 = df_sorted_1.head(top_index)
      top_3_2 = df_sorted_2.head(top_index)
      top_3_3 = df_sorted_3.head(top_index)

      return top_3_1, top_3_2, top_3_3

  def get_features_in_common(self, df1, df2, df3):
      means_all, means_lime, means_shap, means_grad = self.concat_all_mothods(df1, df2, df3)
      top_3_1, top_3_2, top_3_3 = self.get_top_features(means_lime, means_shap, means_grad, 3 )

      df_concat = pd.concat([top_3_1, top_3_2, top_3_3])
      # Contar a frequência de cada valor na coluna 'Coluna'
      coluna_counts = df_concat['Column'].value_counts()
      # Filtrar os valores que aparecem mais de uma vez
      repeated_sensors = coluna_counts[coluna_counts > 1].index
      # Criar um novo DataFrame com as linhas que têm 'Coluna' repetida
      df_final = df_concat[df_concat['Column'].isin(repeated_sensors)]

      return df_final.sort_values(by='Column')
  
  def get_sensor_repeats(self, df_final):
      coluna_counts = df_final['Column'].value_counts()
      df_counts = pd.DataFrame({
          'Sensors': coluna_counts.index,
          'Repeats': coluna_counts.values
      })
      return df_counts.sort_values(by='Sensors').reset_index(drop=True)

  def get_dict_by_query(self, query_sql, conn):
      cursor = conn.cursor()
      cursor.execute(query_sql)
      conn.commit()
      result = cursor.fetchall()
      result_dict = {}
      for data, category, count in result:
          if data not in result_dict:
              result_dict[data] = {}
          result_dict[data][category] = count
      return result_dict, result

  # Função para verificar compatibilidade e retornar os 3 fungos mais compatíveis
  def find_top_compatible_fungi(self, sensor,fungi_dict,sensor_dict ):
      sensor_categories = sensor_dict.get(sensor, {})
      compatibility = []

      for fungus, categories in fungi_dict.items():
          common_categories = set(sensor_categories.keys()).intersection(categories.keys())
          if len(common_categories) >= 1:
              common_details = {category: (sensor_categories[category], categories[category]) for category in common_categories}
              compatibility.append((fungus, len(common_categories), common_details))

      # Ordenar por número de categorias compatíveis (maior para menor)
      compatibility.sort(key=lambda x: x[1], reverse=True)

      # Ordenar as categorias compatíveis por quantidade de repetições (maior para menor)
      for i in range(len(compatibility)):
          compatibility[i] = (compatibility[i][0], compatibility[i][1], dict(sorted(compatibility[i][2].items(), key=lambda item: item[1][1], reverse=True)))

      # Retornar os 3 fungos mais compatíveis
      return compatibility[:3]

  def plot_samples_db(self, data):
    for i, cycle in enumerate(data):
        a = np.array(cycle)[0]
        new_df = self.group_sensor(self.features_name, a)
        self.plot_chart_line_df(new_df)

  def group_sensor(self, features_name, row_cycle):
        # Converte a lista de pesos em um array NumPy para facilitar a manipulação
        weight_array = np.array(row_cycle)
        # Calcula o número de linhas que o DataFrame terá
        num_rows = len(row_cycle) // len(features_name)
        # Redimensiona o array para ter 'num_rows' linhas e 'len(features_name)' colunas
        reshaped_array = weight_array[:num_rows * len(features_name)].reshape(num_rows, len(features_name))

        # Cria o DataFrame a partir do array redimensionado
        df = pd.DataFrame(reshaped_array, columns=features_name)

        return df
  # Adicionando uma coluna de índice para o eixo X
  def plot_chart_line_df(self, dataFrame):
      dataFrame['Index'] = dataFrame.index
      # Transformando o DataFrame para o formato longo
      df_long = pd.melt(dataFrame, id_vars=['Index'], var_name='Sensor', value_name='Valor')
      # Plotando o gráfico de linha
      plt.figure(figsize=(14, 8))
      sns.lineplot(data=df_long, x='Index', y='Valor', hue='Sensor')
      plt.xlabel('Index')
      plt.ylabel('Value')
      plt.title('Line chart sensors')
      plt.legend(title='Sensors')
      plt.show()

  def ploat_heatmap(self, dataFrame):
      fig = px.density_heatmap(dataFrame, x='Feature', y='Weight', nbinsx=20, nbinsy=20, color_continuous_scale='Viridis')
      # Atualizar o layout para permitir zoom e melhor visualização
      fig.update_layout(
          title='Dynamic Heatmap of Feature Weightss',
          xaxis=dict(title='Feature'),
          yaxis=dict(title='Weight'),
          autosize=True
      )
      # Mostrar o mapa de calor
      fig.show()

  def ploat_bar(self, dataFrame):
      fig = px.bar(dataFrame, x='Feature', y='Weight', color='Weight', color_continuous_scale='Viridis')
      # Atualizar o layout para permitir zoom e melhor visualização
      fig.update_layout(
          title='Feature Weights Bar Chart',
          xaxis=dict(title='Feature'),
          yaxis=dict(title='Weight'),
          autosize=True
      )
      # Mostrar o gráfico de barras
      fig.show()

"""# **LIME METHOD**"""

class LIME_Method:
  def __init__(self, api):
    self.api = api
    pass
  def run_LIME_Method(self, train_data, test_data,sample_index, model, class_names):
    print("Running LIME...")
    feature_names = np.array(range(train_data.shape[1]))
    explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=train_data,
        feature_names=feature_names,
        class_names=class_names,
        discretize_continuous=False  # ou True, dependendo da natureza dos seus dados
    )
    num_features = train_data.shape[1]
    instance = test_data[sample_index]
    explanation = explainer.explain_instance(
        instance,
        model.predict,
        num_features= num_features
    )
    # Print the explanation
    feature , weigths = zip(*sorted(explanation.as_list()))
    weigths_array = np.array(weigths)
    return explanation, feature , weigths_array

  def run_mulltiple_LIME_Method(self, train_data, test_data,sample_index, model, class_names,REPEATS):
      print("Running LIME...")
      df_results = []
      for i in range(REPEATS):
          print(f"Cicle: {i+1} of {REPEATS}...")
          explanation, index, wiegths = self.run_LIME_Method(train_data=train_data, test_data=test_data, sample_index=sample_index, model=model, class_names=class_names)
          dataFrame = self.api.create_df(wiegths, index)
          df = self.api.get_most_important_features(dataFrame, 3)
          df_results.append(df)
      return self.summarize_df(df_results)

  def summarize_df(self, df_results):
      #Colocar isso em um método
      df_final = pd.concat(df_results, ignore_index=True)
      # Contar a frequência de cada valor na coluna 'Coluna'
      coluna_counts = df_final['Column'].value_counts()

      # Filtrar os valores que aparecem mais de uma vez
      repeated_sensors = coluna_counts[coluna_counts > 1].index

      # Criar um novo DataFrame com as linhas que têm 'Coluna' repetida
      df_final = df_final[df_final['Column'].isin(repeated_sensors)]

      # Calcular a média das colunas repetidas
      df_final = df_final.groupby('Column').mean().reset_index()

      df_final = df_final.sort_values(by='Column')
      return df_final

  def plot_bar_chart(self, df_final):
      # Configurar o estilo do Seaborn
      sns.set(style="whitegrid")

      # Criar o gráfico de barras
      plt.figure(figsize=(12, 8))
      barplot = sns.barplot(x='Column', y='Mean', hue='Column', data=df_final, palette='viridis')

      # Adicionar títulos e rótulos
      plt.xlabel('Sensors')
      plt.ylabel('Average')
      plt.title(f"DataFrame Sensors Averages to {df_final.DataFrame[0]}")

      # Mostrar o gráfico
      plt.show()

  def plot_class_proba(self, class_name, explanation):
      # Seus valores de probabilidade
      probabilidades = explanation.predict_proba
      # Nomes das classes para o eixo x do gráfico
      plt.figure(figsize=(10, 7))  # Ajuste o tamanho conforme necessário
      # Criar o gráfico de barras
      plt.bar(class_name, probabilidades)

      # Adicionar título e rótulos aos eixos
      plt.title('Probabilidades das Classes')
      plt.xlabel('Classes')
      plt.ylabel('Probabilidade')

      # Mostrar o gráfico
      plt.show()


"""# **SHAP METHOD**"""

class SHAP_Method:
  def __init__(self, features_name, api):
    self.api = api
    self.features_name = features_name
  def run_SHAP_Method(self, train_data, test_data,sample_index, model, class_names, npermutations):
    # explainer = shap.KernelExplainer(model.predict, train_data)
    print("Running SHAP...")
    explainer = shap.PermutationExplainer(model.predict, train_data)
    shap_values = explainer.shap_values(test_data[sample_index-1:sample_index], npermutations=npermutations)

    predicted_classes, main_class_predicted = self.get_model_results(model, test_data,sample_index )

    feature_weights = shap_values[:,:,main_class_predicted][0]  # Sum weights across classes #max_index

    return explainer,shap_values, feature_weights
  
  def run_mulltiple_SHAP_Method(self, train_data, test_data,sample_index, model, class_names, npermutations, REPEATS):
      print("Running SHAP...")
      df_results = []
      for i in range(REPEATS):
          print(f"Cicle: {i+1} of {REPEATS}...")
          explanation, index, wieghts = self.run_SHAP_Method(train_data=train_data, test_data=test_data, sample_index=sample_index, model=model, class_names=class_names, npermutations=npermutations)
          dataFrame = self.api.create_df_2(wieghts)
          df = self.api.get_most_important_features(dataFrame, 3)
          df_results.append(df)
      return self.summarize_df(df_results)

  def get_model_results(self, model, test_data, sample_index):
      predicted_classes = model.predict(test_data[sample_index-1:sample_index])
      main_class_predicted = np.argmax(predicted_classes)
      return predicted_classes, main_class_predicted

  def summarize_df(self, df_results):
      #Colocar isso em um método
      df_final = pd.concat(df_results, ignore_index=True)
      # Contar a frequência de cada valor na coluna 'Coluna'
      coluna_counts = df_final['Column'].value_counts()

      # Filtrar os valores que aparecem mais de uma vez
      repeated_sensors = coluna_counts[coluna_counts > 1].index

      # Criar um novo DataFrame com as linhas que têm 'Coluna' repetida
      df_final = df_final[df_final['Column'].isin(repeated_sensors)]

      df_final = df_final.sort_values(by='Column')
      return df_final

  def plot_bar_chart(self, df_final):
      # Configurar o estilo do Seaborn
      sns.set(style="whitegrid")

      # Criar o gráfico de barras
      plt.figure(figsize=(12, 8))
      barplot = sns.barplot(x='Column', y='Mean', hue='Column', data=df_final, palette='viridis')

      # Adicionar títulos e rótulos
      plt.xlabel('Sensors')
      plt.ylabel('Average')
      plt.title(f"DataFrame Sensors Averages to {df_final.DataFrame[0]}")

      # Mostrar o gráfico
      plt.show()

"""# **GRAD-CAM**"""

class GRAD_CAM_Method:
  def __init__(self, features_name, api):
    self.api = api
    self.features_name = features_name

  def run_GRAD_CAM_Method(self, test_data,sample_index, model, class_names, last_layer_name):
      # Selecionar uma instância para visualização
      print("Running GRAD_CAM...")
      instancia = test_data[sample_index]  # Por exemplo, a primeira instância do conjunto de dados

      # Preparar a instância para o modelo (adicionar uma dimensão extra se necessário)
      instancia = np.expand_dims(instancia, axis=0)

      # Obter a saída do modelo para a instância selecionada
      predicao = model.predict(instancia)

      # Obter a classe prevista
      classe_prevista = np.argmax(predicao[0])

      # Obter o output do último layer convolucional
      ultimo_conv_layer = model.get_layer(last_layer_name) #em alguns casos, isso pode mudar

      # Criar um modelo para Grad-CAM
      grad_model = tf.keras.models.Model(
          [model.inputs],
          [ultimo_conv_layer.output, model.output]
      )

      # Obter os gradientes da classe prevista em relação ao último layer convolucional
      with tf.GradientTape() as tape:
          conv_outputs, predictions = grad_model(instancia)
          predictions = tf.convert_to_tensor(predictions)  # Converter para tensor

          # Verificar o tamanho de predictions
          num_classes = predictions.shape[-1]
          if classe_prevista >= num_classes:
              raise ValueError(f"Classe prevista ({classe_prevista}) está fora dos limites (0 a {num_classes-1}).")

          # Garantir que predictions é um tensor de float32
          predictions = tf.cast(predictions, tf.float32)
          print(predictions[0][0][classe_prevista])
          loss = predictions[0][0][classe_prevista] #predictions[:, classe_prevista]

      # Gradientes em relação à saída do último layer convolucional
      grads = tape.gradient(loss, conv_outputs)[0]

      # Média ponderada dos canais da saída do layer convolucional
      pooled_grads = tf.reduce_mean(grads, axis=(0, 1))

      # Multiplicar cada canal na saída do feature map pelo "importance" desse canal
      heatmap = tf.reduce_sum(tf.multiply(pooled_grads, conv_outputs[0]), axis=-1)
      return heatmap, grad_model, classe_prevista

  def summarize_df(self, df_results):
      # Concatenar os DataFrames
      df_final = pd.concat(df_results, ignore_index=True)

      # Contar a frequência de cada valor na coluna 'Coluna'
      coluna_counts = df_final['Column'].value_counts()

      # Filtrar os valores que aparecem mais de uma vez
      repeated_sensors = coluna_counts[coluna_counts > 1].index

      # Criar um novo DataFrame com as linhas que têm 'Coluna' repetida
      df_final = df_final[df_final['Column'].isin(repeated_sensors)]

      # Calcular a média das colunas repetidas
      df_final = df_final.groupby('Column').mean().reset_index()

      # Ordenar o DataFrame final pela coluna 'Coluna'
      df_final = df_final.sort_values(by='Column')

      return df_final

  def run_mulltiple_GRAD_Method(self, test_data,sample_index, model, class_names,last_layer_name, REPEATS):
      print("Running GRAD_CAM...")
      df_results = []
      for i in range(REPEATS):
          print(f"Cicle: {i+1} of {REPEATS}...")
          heatmap, grad_model, classe_prevista = self.run_GRAD_CAM_Method(test_data=test_data, sample_index=sample_index, model=model, class_names=class_names,last_layer_name=last_layer_name)
          dataFrame = self.api.create_df_2(heatmap)
          df = self.api.get_most_important_features(dataFrame, 3)
          df_results.append(df)
      return self.summarize_df(df_results)

  def plot_heatmap(self, df_grad):
      # Criar o gráfico de barras
      fig = px.bar(df_grad, x='Feature', y='Weight', color='Weight', color_continuous_scale='Viridis')

      # Atualizar o layout para permitir zoom e melhor visualização
      fig.update_layout(
          title='Gráfico de Barras dos Pesos das Características (Grad-CAM)',
          xaxis=dict(title='Feature'),
          yaxis=dict(title='Weight'),
          autosize=True
      )

      # Mostrar o gráfico de barras
      fig.show()

  def plot_bar_chart(self, df_final):
      # Configurar o estilo do Seaborn
      sns.set(style="whitegrid")

      # Criar o gráfico de barras
      plt.figure(figsize=(12, 8))
      barplot = sns.barplot(x='Column', y='Mean', hue='Column', data=df_final, palette='viridis')

      # Adicionar títulos e rótulos
      plt.xlabel('Sensors')
      plt.ylabel('Average')
      plt.title(f"DataFrame Sensors Averages to {df_final.DataFrame[0]}")

      # Mostrar o gráfico
      plt.show()

"""# **Run all methods**"""

class Run_methods:
  def __init__(self, api):
      self.api = api
      self.LIME = LIME_Method(self.api)
      self.SHAP = SHAP_Method(self.api.features_name, self.api)
      self.GRAD = GRAD_CAM_Method(self.api.features_name, self.api)

  def run_all_methods_mult(self, X_train, X_test,sample_index, model, class_names, npermutations, last_layer_name, REPEATS):

      df_LIME = self.LIME.run_mulltiple_LIME_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names, REPEATS=REPEATS)
      df_shap = self.SHAP.run_mulltiple_SHAP_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names, npermutations=npermutations, REPEATS=REPEATS)
      df_GRAD = self.GRAD.run_mulltiple_GRAD_Method(test_data=X_test, sample_index=sample_index, model=model,class_names=class_names, last_layer_name=last_layer_name, REPEATS=REPEATS)

      df_final = self.api.get_features_in_common(df_LIME, df_shap, df_GRAD)
      df_caounts = self.api.get_sensor_repeats(df_final)

      return df_LIME, df_shap, df_GRAD, df_final, df_caounts

  def run_2_methods_mult(self, X_train, X_test, sample_index, model, class_names,last_layer_name, REPEATS):

      df_LIME = self.LIME.run_mulltiple_LIME_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names, REPEATS=REPEATS)
      df_shap = pd.DataFrame(data={'Column':[0],'Mean':[0],'DataFrame':'SHAP'})
      df_GRAD = self.GRAD.run_mulltiple_GRAD_Method(test_data=X_test, sample_index=sample_index, model=model,class_names=class_names, last_layer_name=last_layer_name, REPEATS=REPEATS)

      df_final = self.api.get_features_in_common(df_LIME, df_shap, df_GRAD)
      df_caounts = self.api.get_sensor_repeats(df_final)

      return df_LIME, df_shap, df_GRAD, df_final, df_caounts

  def run_all_methods_once(self, X_train, X_test,sample_index, model, class_names, npermutations,last_layer_name):

      explanation, index, wiegths = self.LIME.run_LIME_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names)
      dataFrame_1 = self.api.create_df(wiegths, index)
      df_LIME = self.api.get_most_important_features(dataFrame_1, 3)

      explainer,shap_values, feature_weights = self.SHAP.run_SHAP_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names, npermutations=npermutations)
      dataFrame_2 = self.api.create_df_2(list_weights=feature_weights)
      df_shap = self.api.get_most_important_features(dataFrame_2, 3)
     
      heatmap, grad_model, classe_prevista = self.GRAD.run_GRAD_CAM_Method(test_data=X_test, sample_index=sample_index, model=model,class_names=class_names, last_layer_name=last_layer_name)
      dataFrame_3 = self.api.create_df_2(heatmap)
      df_GRAD = self.api.get_most_important_features(dataFrame_3, 3)

      df_final = self.api.get_features_in_common(df_LIME, df_shap, df_GRAD)
      df_caounts = self.api.get_sensor_repeats(df_final)

      return df_LIME, df_shap, df_GRAD, df_final, df_caounts

  def run_2_methods_once(self, X_train, X_test,sample_index, model, class_names, last_layer_name):

      explanation, index, wiegths = self.LIME.run_LIME_Method(train_data=X_train, test_data=X_test, sample_index=sample_index, model=model, class_names=class_names)
      dataFrame_1 = self.api.create_df(wiegths, index)
      df_LIME = self.api.get_most_important_features(dataFrame_1, 3)

      df_shap = pd.DataFrame(data={'Column':[0],'Mean':[0],'DataFrame':'SHAP'})

      heatmap, grad_model, classe_prevista = self.GRAD.run_GRAD_CAM_Method(test_data=X_test, sample_index=sample_index, model=model,class_names=class_names, last_layer_name=last_layer_name)
      dataFrame_3 = self.api.create_df_2(heatmap)
      df_GRAD = self.api.get_most_important_features(dataFrame_3, 3)

      df_final = self.api.get_features_in_common(df_LIME, df_shap, df_GRAD)
      df_caounts = self.api.get_sensor_repeats(df_final)

      return df_LIME, df_shap, df_GRAD, df_final, df_caounts

  def plot_all_bar_charts(self,df_LIME, df_shap, df_GRAD):
      self.LIME.plot_bar_chart(df_LIME)
      if(df_shap.Mean.mean() !=0):
        self.SHAP.plot_bar_chart(df_shap)

      self.GRAD.plot_bar_chart(df_GRAD)

  def print_result(self, df_caounts, db_name, query_fungi, query_sensor):
      import sqlite3
      conn = sqlite3.connect(db_name)
      fungi_dict, fungi = self.api.get_dict_by_query(query_fungi,conn)
      sensor_dict, sensor = self.api.get_dict_by_query(query_sensor,conn)

      for sensor in df_caounts.Sensors:
        #   print(sensor)
          top_fungi = self.api.find_top_compatible_fungi(sensor,fungi_dict,sensor_dict)
          print(f"Os 3 fungos mais compatíveis com o sensor {sensor} são:")
          for fungus, count, details in top_fungi:
              print(f"{fungus} com {count} categorias compatíveis:")
              for category, (sensor_count, fungus_count) in details.items():
                  print(f"  - {category}: Sensor ({sensor_count} vezes), Fungo ({fungus_count} vezes)")
              print()

  def plot_bar_chart_all_methods(self, dataFrame):
      sns.set(style="whitegrid")
      # Criando a figura com maior DPI e tamanho
      plt.figure(figsize=(12, 8), dpi=200)

      # Criando o gráfico de barras
      sns.barplot(x='Column', y='Mean', hue='DataFrame', data=dataFrame, palette='viridis')

      # Adicionando labels e título
      plt.xlabel('Sensors', fontweight='bold')
      plt.ylabel('Average values', fontweight='bold')
      plt.title('DataFrame Sensors Averages')

      # Rotacionando os nomes das colunas no eixo X
      plt.xticks(rotation=45)

      # Exibindo o gráfico
      plt.show()

"""# **Teste**"""

# features_name = ["TGS-826","TGS-2611","TGS-2603","TGS-813","TGS-822","TGS-2602","TGS-823"]
# class_names = ['Albicans', 'Glabrata', 'Haemulonii', 'Kodamaea_ohmeri', 'Krusei', 'Parapsilosis']
# api = ExplainableAPI(features_name)
# X_train, y_train = api.load_data(path="AllCandidas_TRAIN.csv", sep=",")  # Replace with actual path and separator
# X_test, y_test = api.load_data(path="AllCandidas_TEST.csv", sep=",")  # Replace with actual path and separator
# SAMPLE_INDEX = 3# amostra que será selecionada do df de teste
# model = tf.keras.models.load_model('/content/best_model.hdf5')

# main = Run_methods(api)
